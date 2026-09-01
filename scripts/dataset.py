"""Freeze, verify and list hash-checked candle datasets (T6).

Usage:
    python scripts/dataset.py freeze --name btc-eth-spot-binance --version v1 \
        --symbols BTCUSDT,ETHUSDT --timeframes 1m,5m,15m,1h,4h,1d \
        --start 2017-08-17 --end 2026-08-30
    python scripts/dataset.py verify --name btc-eth-spot-binance --version v1
    python scripts/dataset.py verify --name ... --version v1 --symbol BTCUSDT --timeframe 1h
    python scripts/dataset.py list

verify exits 1 on any divergence (fail-closed, ADR-0001 décision 6).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import UTC, datetime

from quantlab.core.config import AppConfig
from quantlab.core.logging import configure_logging
from quantlab.data.binance.source import SOURCE_BINANCE
from quantlab.data.datasets import (
    SeriesResolver,
    VerifyReport,
    freeze_dataset,
    verify_dataset,
    verify_series,
)
from quantlab.domain.models import Timeframe
from quantlab.storage.postgres.adapter import (
    PostgresAuditEventWriter,
    PostgresCandleRepository,
    PostgresDataQualityEventRepository,
    PostgresDatasetRepository,
    PostgresInstrumentRepository,
    PostgresVenueRepository,
)


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)


def code_commit() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10
        )
        return out.stdout.strip() or None if out.returncode == 0 else None
    except OSError:
        return None


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    fz = sub.add_parser("freeze", help="publish an immutable hash-checked dataset")
    fz.add_argument("--name", required=True)
    fz.add_argument("--version", required=True)
    fz.add_argument("--symbols", required=True, help="comma-separated venue symbols")
    fz.add_argument("--timeframes", required=True, help="comma-separated timeframes")
    fz.add_argument("--start", required=True)
    fz.add_argument("--end", required=True)
    fz.add_argument("--venue", default="BINANCE")

    vf = sub.add_parser("verify", help="recompute hashes and compare (exit 1 on divergence)")
    vf.add_argument("--name", required=True)
    vf.add_argument("--version", required=True)
    vf.add_argument("--symbol", help="verify one series only (with --timeframe)")
    vf.add_argument("--timeframe", choices=[tf.value for tf in Timeframe])

    sub.add_parser("list", help="list published datasets")

    args = parser.parse_args(argv)
    if args.command == "verify" and bool(args.symbol) != bool(args.timeframe):
        parser.error("--symbol and --timeframe go together")
    return args


def print_report(report: VerifyReport) -> None:
    if report.ok:
        print(f"VERIFY OK: {report.dataset_name}@{report.version} ({report.candle_count} candles)")
        return
    print(f"VERIFY FAILED: {report.dataset_name}@{report.version}", file=sys.stderr)
    for m in report.mismatches:
        print(
            f"  {m.venue_symbol} {m.timeframe.value} [{m.kind}] "
            f"expected={m.expected} actual={m.actual}",
            file=sys.stderr,
        )


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    url = os.environ.get("QUANTLAB_DATABASE_URL")
    if not url:
        print("QUANTLAB_DATABASE_URL is not set", file=sys.stderr)
        return 2
    configure_logging(AppConfig.load().log_level)

    candles = PostgresCandleRepository(url)
    datasets = PostgresDatasetRepository(url)
    quality = PostgresDataQualityEventRepository(url)
    audit = PostgresAuditEventWriter(url)
    venues = PostgresVenueRepository(url)
    instruments = PostgresInstrumentRepository(url)
    resolve = SeriesResolver(venues, instruments)

    if args.command == "list":
        for ds in datasets.list_all():
            meta = ds.metadata or {}
            print(
                f"{ds.dataset_name}@{ds.version}  {ds.content_hash[:16]}…  "
                f"{meta.get('total_candles', '?')} candles  "
                f"[{ds.start_time.isoformat()} → {ds.end_time.isoformat()})  "
                f"created {ds.created_at.isoformat() if ds.created_at else '?'}"
            )
        return 0

    if args.command == "freeze":
        venue = venues.get_by_code(args.venue)
        if venue is None:
            print(f"venue {args.venue!r} not found — run `make seed`", file=sys.stderr)
            return 1
        selections = []
        for symbol in args.symbols.split(","):
            instrument = instruments.get_by_venue_symbol(venue.venue_id, symbol.strip())
            if instrument is None:
                print(f"instrument {symbol!r} not found on {args.venue}", file=sys.stderr)
                return 1
            selections.append((venue, instrument))
        timeframes = [Timeframe(tf.strip()) for tf in args.timeframes.split(",")]

        dataset = freeze_dataset(
            candles,
            datasets,
            audit,
            args.name,
            args.version,
            selections,
            timeframes,
            parse_utc(args.start),
            parse_utc(args.end),
            SOURCE_BINANCE,
            code_commit=code_commit(),
        )
        meta = dataset.metadata or {}
        print(
            f"FROZEN: {dataset.dataset_name}@{dataset.version}\n"
            f"content_hash={dataset.content_hash}\n"
            f"series={len(meta.get('series', []))} total_candles={meta.get('total_candles')}"
        )
        return 0

    if args.symbol:
        report = verify_series(
            candles,
            datasets,
            resolve,
            quality,
            audit,
            args.name,
            args.version,
            args.symbol,
            Timeframe(args.timeframe),
        )
    else:
        report = verify_dataset(candles, datasets, resolve, quality, audit, args.name, args.version)
    print_report(report)
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

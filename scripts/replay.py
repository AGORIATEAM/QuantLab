"""Replay a published dataset under a simulated clock (T7).

Usage:
    python scripts/replay.py --dataset btc-eth-spot-binance --version v1 \
        [--symbols BTCUSDT] [--timeframes 1m] [--start ... --end ... --lookback-hours N] \
        --benchmark

--benchmark consumes the stream discarding events and reports verify time,
stream time and candles/s — the Phase 2 sizing numbers.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import UTC, datetime, timedelta

from quantlab.core.clock import SimulatedClock
from quantlab.core.config import AppConfig
from quantlab.core.logging import configure_logging
from quantlab.data.datasets import SeriesResolver
from quantlab.data.replay import ReplayReport, replay_candles
from quantlab.domain.models import Timeframe
from quantlab.storage.postgres.adapter import (
    PostgresAuditEventWriter,
    PostgresCandleSnapshotFactory,
    PostgresDataQualityEventRepository,
    PostgresDatasetRepository,
    PostgresInstrumentRepository,
    PostgresVenueRepository,
)


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--symbols", help="comma-separated subset")
    parser.add_argument("--timeframes", help="comma-separated subset")
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--lookback-hours", type=float)
    parser.add_argument("--benchmark", action="store_true", help="consume and time the stream")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    url = os.environ.get("QUANTLAB_DATABASE_URL")
    if not url:
        print("QUANTLAB_DATABASE_URL is not set", file=sys.stderr)
        return 2
    configure_logging(AppConfig.load().log_level)

    datasets = PostgresDatasetRepository(url)
    dataset = datasets.get(args.dataset, args.version)
    if dataset is None:
        print(f"dataset {args.dataset}@{args.version} not found", file=sys.stderr)
        return 1

    start = parse_utc(args.start) if args.start else dataset.start_time
    clock = SimulatedClock(start)
    report = ReplayReport()
    stream = replay_candles(
        PostgresCandleSnapshotFactory(url),
        datasets,
        SeriesResolver(PostgresVenueRepository(url), PostgresInstrumentRepository(url)),
        PostgresDataQualityEventRepository(url),
        PostgresAuditEventWriter(url),
        args.dataset,
        args.version,
        clock,
        symbols=args.symbols.split(",") if args.symbols else None,
        timeframes=[Timeframe(tf) for tf in args.timeframes.split(",")]
        if args.timeframes
        else None,
        start=parse_utc(args.start) if args.start else None,
        end=parse_utc(args.end) if args.end else None,
        lookback=timedelta(hours=args.lookback_hours) if args.lookback_hours else None,
        report=report,
    )

    shown = 0
    for event in stream:
        if not args.benchmark and shown < 5:
            shown += 1
            c = event.candle
            tag = "warmup " if event.is_warmup else ""
            print(
                f"{tag}{event.series.venue_symbol} {c.timeframe.value} "
                f"{c.open_time.isoformat()} close={c.close}"
            )

    rate = round(report.emitted / report.stream_seconds) if report.stream_seconds > 0 else 0
    print(
        f"replayed {args.dataset}@{args.version}: {report.emitted} candles "
        f"({report.warmup} warmup) — verify {report.verify_seconds:.1f}s, "
        f"stream {report.stream_seconds:.1f}s, {rate} candles/s, "
        f"clock ended at {clock.now().isoformat()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

"""Scan a stored candle series for gaps; optionally backfill them (T5).

Usage:
    python scripts/scan_gaps.py --symbol BTCUSDT --timeframe 1h \
        --start 2017-08-17 [--end 2026-08-30] [--backfill]

Without --end the scan stops at the last closed candle boundary (now, floored
to the timeframe grid). The scan records one GAP quality event per hole and is
idempotent. With --backfill, every unresolved GAP is refetched from the venue;
sub-ranges the venue does not serve are reclassified KNOWN_VENUE_GAP, and a
final rescan prints the resulting state of the series.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import UTC, datetime

from quantlab.core.config import AppConfig
from quantlab.core.logging import configure_logging
from quantlab.core.timeutils import utc_now
from quantlab.data.binance.client import BinanceRestClient
from quantlab.data.binance.source import SOURCE_BINANCE, BinanceCandleSource
from quantlab.data.gaps import GapScanReport, align_down, backfill_gaps, scan_gaps
from quantlab.domain.models import Timeframe
from quantlab.storage.postgres.adapter import (
    PostgresAuditEventWriter,
    PostgresCandleRepository,
    PostgresDataQualityEventRepository,
    PostgresInstrumentRepository,
    PostgresVenueRepository,
)


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbol", required=True, help="venue symbol, e.g. BTCUSDT")
    parser.add_argument("--timeframe", required=True, choices=[tf.value for tf in Timeframe])
    parser.add_argument("--start", required=True, help="ISO date/datetime, UTC assumed if naive")
    parser.add_argument("--end", help="default: last closed candle boundary (now)")
    parser.add_argument("--venue", default="BINANCE")
    parser.add_argument("--limit", type=int, default=1000, help="candles per API request")
    parser.add_argument("--backfill", action="store_true", help="refetch unresolved gaps")
    return parser.parse_args(argv)


def print_report(label: str, report: GapScanReport) -> None:
    print(
        f"{label}: {len(report.holes)} hole(s) over "
        f"[{report.start.isoformat()} → {report.end.isoformat()}), "
        f"{report.new_events} new GAP event(s), {report.already_known} already known"
    )
    for hole in report.holes:
        status = "known" if hole.already_known else "NEW"
        print(
            f"  {hole.start.isoformat()} → {hole.end.isoformat()} "
            f"({hole.expected_candles} candles) [{status}]"
        )


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    url = os.environ.get("QUANTLAB_DATABASE_URL")
    if not url:
        print("QUANTLAB_DATABASE_URL is not set", file=sys.stderr)
        return 2
    configure_logging(AppConfig.load().log_level)

    timeframe = Timeframe(args.timeframe)
    start = parse_utc(args.start)
    end = parse_utc(args.end) if args.end else align_down(utc_now(), timeframe.duration)

    venue = PostgresVenueRepository(url).get_by_code(args.venue)
    if venue is None:
        print(f"venue {args.venue!r} not found — run `make seed` first", file=sys.stderr)
        return 1
    instrument = PostgresInstrumentRepository(url).get_by_venue_symbol(venue.venue_id, args.symbol)
    if instrument is None:
        print(f"instrument {args.symbol!r} not found on {args.venue}", file=sys.stderr)
        return 1

    candles = PostgresCandleRepository(url)
    quality = PostgresDataQualityEventRepository(url)
    audit = PostgresAuditEventWriter(url)

    report = scan_gaps(candles, quality, audit, instrument, timeframe, start, end, SOURCE_BINANCE)
    print_report("scan", report)
    if not args.backfill:
        return 0

    with BinanceRestClient() as client:
        source = BinanceCandleSource(client, quality)
        result = backfill_gaps(
            source, candles, quality, audit, instrument, timeframe, SOURCE_BINANCE, args.limit
        )
    print(
        f"backfill: gaps_processed={result.gaps_processed} inserted={result.inserted} "
        f"filled={result.filled} known_venue_gaps={result.known_venue_gaps}"
    )

    rescan = scan_gaps(candles, quality, audit, instrument, timeframe, start, end, SOURCE_BINANCE)
    print_report("rescan", rescan)
    if rescan.new_events:
        print("rescan found unexpected new holes", file=sys.stderr)
        return 1
    print("series clean: every hole is filled or classified KNOWN_VENUE_GAP")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

"""Download historical candles from Binance public REST into PostgreSQL.

Usage:
    python scripts/download_history.py --symbol BTCUSDT --timeframe 1h \
        --start 2025-07-01 --end 2025-08-01
    python scripts/download_history.py --smoke

--smoke is the reduced-scope preset used before any full download: BTCUSDT,
1h, the last 30 days (~720 candles, one API request).

Resumable: rerunning continues after the newest stored candle for the same
(instrument, timeframe, source); a rerun over a covered range inserts nothing.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import UTC, datetime, timedelta

from quantlab.core.config import AppConfig
from quantlab.core.logging import configure_logging
from quantlab.core.timeutils import utc_now
from quantlab.data.binance.client import BinanceRestClient
from quantlab.data.binance.source import SOURCE_BINANCE, BinanceCandleSource
from quantlab.data.download import download_history
from quantlab.domain.models import Timeframe
from quantlab.storage.postgres.adapter import (
    PostgresAuditEventWriter,
    PostgresCandleRepository,
    PostgresDataQualityEventRepository,
    PostgresInstrumentRepository,
    PostgresVenueRepository,
)

SMOKE_SYMBOL = "BTCUSDT"
SMOKE_TIMEFRAME = Timeframe.H1
SMOKE_DAYS = 30


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbol", help="venue symbol, e.g. BTCUSDT")
    parser.add_argument("--timeframe", choices=[tf.value for tf in Timeframe])
    parser.add_argument("--start", help="ISO date/datetime, UTC assumed if naive")
    parser.add_argument("--end", help="ISO date/datetime, UTC assumed if naive")
    parser.add_argument("--venue", default="BINANCE")
    parser.add_argument("--limit", type=int, default=1000, help="candles per API request")
    parser.add_argument(
        "--smoke",
        action="store_true",
        help=f"reduced-scope smoke preset: {SMOKE_SYMBOL} {SMOKE_TIMEFRAME.value}, "
        f"last {SMOKE_DAYS} days",
    )
    args = parser.parse_args(argv)
    if args.smoke:
        if args.symbol or args.timeframe or args.start or args.end:
            parser.error("--smoke replaces --symbol/--timeframe/--start/--end")
    elif not (args.symbol and args.timeframe and args.start and args.end):
        parser.error("either --smoke or all of --symbol/--timeframe/--start/--end are required")
    return args


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    url = os.environ.get("QUANTLAB_DATABASE_URL")
    if not url:
        print("QUANTLAB_DATABASE_URL is not set", file=sys.stderr)
        return 2
    configure_logging(AppConfig.load().log_level)

    if args.smoke:
        symbol, timeframe = SMOKE_SYMBOL, SMOKE_TIMEFRAME
        end = utc_now()
        start = end - timedelta(days=SMOKE_DAYS)
    else:
        symbol, timeframe = args.symbol, Timeframe(args.timeframe)
        start, end = parse_utc(args.start), parse_utc(args.end)

    venue = PostgresVenueRepository(url).get_by_code(args.venue)
    if venue is None:
        print(f"venue {args.venue!r} not found — run `make seed` first", file=sys.stderr)
        return 1
    instrument = PostgresInstrumentRepository(url).get_by_venue_symbol(venue.venue_id, symbol)
    if instrument is None:
        print(f"instrument {symbol!r} not found on {args.venue} — run `make seed`", file=sys.stderr)
        return 1

    with BinanceRestClient() as client:
        source = BinanceCandleSource(client, PostgresDataQualityEventRepository(url))
        report = download_history(
            source,
            PostgresCandleRepository(url),
            PostgresAuditEventWriter(url),
            instrument,
            timeframe,
            start,
            end,
            SOURCE_BINANCE,
            limit=args.limit,
        )

    print(
        f"{report.venue_symbol} {report.timeframe.value} "
        f"[{report.start.isoformat()} → {report.end.isoformat()})\n"
        f"resumed_from={report.resumed_from.isoformat() if report.resumed_from else 'none'} "
        f"batches={report.batches} fetched={report.fetched} "
        f"inserted={report.inserted} duplicates_skipped={report.duplicates_skipped}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

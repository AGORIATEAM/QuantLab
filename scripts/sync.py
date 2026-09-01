"""Daily data maintenance (T9): incremental REST download of every series,
then gap scan + backfill, then the health report. Exit code = health verdict.

Usage:
    python scripts/sync.py [--symbols ...] [--timeframes ...] [--venue BINANCE]
"""

from __future__ import annotations

import argparse
import os
import sys

from common import add_scope_args, resolve_scope
from quantlab.core.config import AppConfig
from quantlab.core.logging import configure_logging
from quantlab.core.timeutils import utc_now
from quantlab.data.binance.client import BinanceRestClient
from quantlab.data.binance.source import SOURCE_BINANCE, BinanceCandleSource
from quantlab.data.download import download_history
from quantlab.data.gaps import align_down, backfill_gaps, scan_gaps
from quantlab.data.health import DATA_EPOCH, check_health, format_report
from quantlab.storage.postgres.adapter import (
    PostgresAuditEventWriter,
    PostgresCandleRepository,
    PostgresDataQualityEventRepository,
    PostgresRawWsMessageWriter,
)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_scope_args(parser)
    args = parser.parse_args(argv)
    url = os.environ.get("QUANTLAB_DATABASE_URL")
    if not url:
        print("QUANTLAB_DATABASE_URL is not set", file=sys.stderr)
        return 2
    configure_logging(AppConfig.load().log_level)
    instruments, timeframes = resolve_scope(url, args)

    candles = PostgresCandleRepository(url)
    quality = PostgresDataQualityEventRepository(url)
    audit = PostgresAuditEventWriter(url)

    with BinanceRestClient() as client:
        source = BinanceCandleSource(client, quality)
        for instrument in instruments:
            for timeframe in timeframes:
                end = align_down(utc_now(), timeframe.duration)
                report = download_history(
                    source,
                    candles,
                    audit,
                    instrument,
                    timeframe,
                    DATA_EPOCH,
                    end,
                    SOURCE_BINANCE,
                )
                scan = scan_gaps(
                    candles,
                    quality,
                    audit,
                    instrument,
                    timeframe,
                    DATA_EPOCH,
                    end,
                    SOURCE_BINANCE,
                )
                filled = backfill_gaps(
                    source, candles, quality, audit, instrument, timeframe, SOURCE_BINANCE
                )
                print(
                    f"{instrument.venue_symbol}/{timeframe.value}: "
                    f"downloaded={report.inserted} holes={len(scan.holes)} "
                    f"new_gaps={scan.new_events} backfilled={filled.inserted} "
                    f"known_venue_gaps={filled.known_venue_gaps}"
                )

    health = check_health(
        candles,
        quality,
        PostgresRawWsMessageWriter(url),
        audit,
        instruments,
        timeframes,
    )
    print()
    print(format_report(health))
    return 0 if health.healthy else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

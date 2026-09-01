"""Data health report (T9). Exit 0 healthy, 1 stale or holed.

Usage:
    python scripts/health.py [--symbols BTCUSDT,ETHUSDT] [--timeframes ...]
        [--ws-grace 3.0] [--rest-grace-hours 25] [--since-days 7] [--require-ws]
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import timedelta

from common import add_scope_args, resolve_scope
from quantlab.core.config import AppConfig
from quantlab.core.logging import configure_logging
from quantlab.data.health import check_health, format_report
from quantlab.storage.postgres.adapter import (
    PostgresAuditEventWriter,
    PostgresCandleRepository,
    PostgresDataQualityEventRepository,
    PostgresRawWsMessageWriter,
)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    add_scope_args(parser)
    parser.add_argument("--ws-grace", type=float, default=3.0, help="x timeframe duration")
    parser.add_argument("--rest-grace-hours", type=float, default=25.0)
    parser.add_argument("--since-days", type=float, default=7.0, help="WS outage window")
    parser.add_argument("--require-ws", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    url = os.environ.get("QUANTLAB_DATABASE_URL")
    if not url:
        print("QUANTLAB_DATABASE_URL is not set", file=sys.stderr)
        return 2
    configure_logging(AppConfig.load().log_level)
    instruments, timeframes = resolve_scope(url, args)

    report = check_health(
        PostgresCandleRepository(url),
        PostgresDataQualityEventRepository(url),
        PostgresRawWsMessageWriter(url),
        PostgresAuditEventWriter(url),
        instruments,
        timeframes,
        ws_grace_multiplier=args.ws_grace,
        rest_grace=timedelta(hours=args.rest_grace_hours),
        outages_since=timedelta(days=args.since_days),
        require_ws=args.require_ws,
    )
    print(format_report(report))
    return 0 if report.healthy else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

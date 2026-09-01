"""Live WebSocket ingestion for the Phase 1 scope (T8).

Usage:
    python scripts/live_ingest.py [--symbols BTCUSDT,ETHUSDT] \
        [--timeframes 1m,5m,15m,1h,4h,1d] [--venue BINANCE]

Runs until Ctrl-C (SIGINT/SIGTERM): connects to the Binance combined kline
stream, ingests closed klines as source='binance_ws' (raw frames journaled
in raw_ws_messages), reconciles WS outages over REST as source='binance'
(ADR-0001 addendum A). Data only — no execution.
"""

from __future__ import annotations

import argparse
import os
import signal
import sys
from collections.abc import Iterator
from typing import Any

from quantlab.core.config import AppConfig
from quantlab.core.logging import configure_logging
from quantlab.data.binance.client import BinanceRestClient
from quantlab.data.binance.source import BinanceCandleSource
from quantlab.data.binance.ws import BinanceWsClient, combined_stream_url, stream_name
from quantlab.data.live import LiveIngestor, run_live_ingestion
from quantlab.domain.models import Timeframe
from quantlab.storage.postgres.adapter import (
    PostgresAuditEventWriter,
    PostgresCandleRepository,
    PostgresDataQualityEventRepository,
    PostgresInstrumentRepository,
    PostgresRawWsMessageWriter,
    PostgresVenueRepository,
)

DEFAULT_SYMBOLS = "BTCUSDT,ETHUSDT"
DEFAULT_TIMEFRAMES = "1m,5m,15m,1h,4h,1d"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbols", default=DEFAULT_SYMBOLS)
    parser.add_argument("--timeframes", default=DEFAULT_TIMEFRAMES)
    parser.add_argument("--venue", default="BINANCE")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    url = os.environ.get("QUANTLAB_DATABASE_URL")
    if not url:
        print("QUANTLAB_DATABASE_URL is not set", file=sys.stderr)
        return 2
    configure_logging(AppConfig.load().log_level)

    venue = PostgresVenueRepository(url).get_by_code(args.venue)
    if venue is None:
        print(f"venue {args.venue!r} not found — run `make seed`", file=sys.stderr)
        return 1
    instrument_repo = PostgresInstrumentRepository(url)
    instruments = {}
    for symbol in args.symbols.split(","):
        symbol = symbol.strip()
        instrument = instrument_repo.get_by_venue_symbol(venue.venue_id, symbol)
        if instrument is None:
            print(f"instrument {symbol!r} not found on {args.venue}", file=sys.stderr)
            return 1
        instruments[symbol] = instrument
    timeframes = [Timeframe(tf.strip()) for tf in args.timeframes.split(",")]

    streams = [stream_name(symbol, timeframe) for symbol in instruments for timeframe in timeframes]
    ws_url = combined_stream_url(streams)
    print(f"subscribing {len(streams)} streams; Ctrl-C to stop")

    stopping = False

    def request_stop(_signum: int, _frame: Any) -> None:
        nonlocal stopping
        stopping = True
        print("stop requested — finishing current frame…", file=sys.stderr)

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)

    quality = PostgresDataQualityEventRepository(url)
    ingestor = LiveIngestor(
        candles=PostgresCandleRepository(url),
        quality=quality,
        raw_messages=PostgresRawWsMessageWriter(url),
        instruments=instruments,
        timeframes=timeframes,
    )

    def frames() -> Iterator[str]:
        return BinanceWsClient(ws_url).frames()

    with BinanceRestClient() as rest_client:
        rest_source = BinanceCandleSource(rest_client, quality)
        stats = run_live_ingestion(
            frames,
            ingestor,
            rest_source,
            PostgresAuditEventWriter(url),
            should_stop=lambda: stopping,
        )

    print(
        f"stopped: messages={stats.messages} closed={stats.closed_klines} "
        f"archived={stats.archived} inserted={stats.inserted} "
        f"duplicates={stats.duplicates} malformed={stats.malformed} "
        f"outages={stats.outages} reconciled={stats.reconciled} "
        f"last_latency_ms={stats.last_latency_ms}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

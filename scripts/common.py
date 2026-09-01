"""Shared CLI scope resolution for the data scripts (Phase 1 default:
BTC/ETH spot on BINANCE, the six dataset timeframes)."""

from __future__ import annotations

import argparse

from quantlab.domain.models import Instrument, Timeframe
from quantlab.storage.postgres.adapter import (
    PostgresInstrumentRepository,
    PostgresVenueRepository,
)

DEFAULT_SYMBOLS = "BTCUSDT,ETHUSDT"
DEFAULT_TIMEFRAMES = "1m,5m,15m,1h,4h,1d"


def add_scope_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--symbols", default=DEFAULT_SYMBOLS)
    parser.add_argument("--timeframes", default=DEFAULT_TIMEFRAMES)
    parser.add_argument("--venue", default="BINANCE")


def resolve_scope(url: str, args: argparse.Namespace) -> tuple[list[Instrument], list[Timeframe]]:
    venue = PostgresVenueRepository(url).get_by_code(args.venue)
    if venue is None:
        raise SystemExit(f"venue {args.venue!r} not found — run `make seed`")
    repo = PostgresInstrumentRepository(url)
    instruments = []
    for symbol in args.symbols.split(","):
        instrument = repo.get_by_venue_symbol(venue.venue_id, symbol.strip())
        if instrument is None:
            raise SystemExit(f"instrument {symbol!r} not found on {args.venue}")
        instruments.append(instrument)
    return instruments, [Timeframe(tf.strip()) for tf in args.timeframes.split(",")]

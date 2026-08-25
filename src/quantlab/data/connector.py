"""Provider-neutral data source contracts (03-Data-Engine §10, §13).

Engines and the downloader depend on these Protocols only. Venue-specific
clients live in submodules (quantlab.data.binance) and are wired in behind
them, normalization included — no vendor format leaks upward.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from quantlab.domain.models import Candle, Instrument, Timeframe


class HistoricalCandleSource(Protocol):
    """Page-limited access to a venue's historical candles.

    Implementations normalize to domain Candles and never return the candle
    still in progress (look-ahead protection, 03-Data-Engine §40).
    """

    def fetch_candles(
        self,
        instrument: Instrument,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
        limit: int = 1000,
    ) -> list[Candle]:
        """Up to `limit` closed candles with open_time in [start, end),
        strictly ascending, starting at the first available >= start.
        An empty list means the venue has no data left in the range."""
        ...

    def health_check(self) -> bool: ...

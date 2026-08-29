"""Binance implementation of HistoricalCandleSource: REST client + normalization.

This is what the rest of the system consumes — it returns domain Candles only,
never venue payloads (03-Data-Engine §10).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from quantlab.core.timeutils import utc_now
from quantlab.data.binance.client import BinanceRestClient
from quantlab.data.connector import HistoricalCandleSource
from quantlab.data.validate import normalize_and_validate
from quantlab.domain.models import Candle, Instrument, Timeframe
from quantlab.storage.repositories import DataQualityEventRepository

# Provenance tag for candles ingested through the REST connector (ADR-0001 §5);
# the live WebSocket path (T8) will use its own distinct source.
SOURCE_BINANCE = "binance"


class BinanceCandleSource:
    def __init__(
        self,
        client: BinanceRestClient,
        quality_events: DataQualityEventRepository,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        self._client = client
        self._quality_events = quality_events
        self._now = now

    def fetch_candles(
        self,
        instrument: Instrument,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
        limit: int = 1000,
    ) -> list[Candle]:
        raws = self._client.fetch_klines(instrument.venue_symbol, timeframe, start, end, limit)
        return normalize_and_validate(
            raws, instrument, timeframe, SOURCE_BINANCE, self._quality_events, now=self._now()
        )

    def health_check(self) -> bool:
        return self._client.health_check()


def _protocol_conformance(source: BinanceCandleSource) -> HistoricalCandleSource:
    """mypy-checked proof that BinanceCandleSource satisfies the protocol."""
    return source

"""Validation with quarantine (03-Data-Engine §19, §22).

Invalid venue data never crashes the pipeline and is never silently dropped:
each rejected kline produces a DataQualityEvent(INVALID_CANDLE) and the rest
of the batch continues. The candle still in progress (close_time > now) is
excluded without an event — it is simply not closed yet (look-ahead
protection, 03-Data-Engine §40).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from quantlab.core.ids import new_id
from quantlab.core.logging import get_logger
from quantlab.core.timeutils import require_utc, utc_now
from quantlab.data.binance.models import RawKline
from quantlab.data.normalize import normalize_kline
from quantlab.domain.models import (
    Candle,
    DataQualityEvent,
    Instrument,
    QualityCode,
    QualitySeverity,
    Timeframe,
)
from quantlab.storage.repositories import DataQualityEventRepository

logger = get_logger(__name__)


def normalize_and_validate(
    raws: Sequence[RawKline],
    instrument: Instrument,
    timeframe: Timeframe,
    source: str,
    quality_events: DataQualityEventRepository,
    now: datetime | None = None,
) -> list[Candle]:
    """Normalize a batch of raw klines into closed, valid domain Candles."""
    current = utc_now() if now is None else require_utc(now, "now")
    candles: list[Candle] = []
    for raw in raws:
        try:
            candle = normalize_kline(raw, instrument.instrument_id, timeframe, source)
        except ValueError as exc:
            quality_events.insert(
                DataQualityEvent(
                    event_id=new_id(),
                    dataset_type="candles",
                    instrument_id=instrument.instrument_id,
                    severity=QualitySeverity.ERROR,
                    code=QualityCode.INVALID_CANDLE,
                    event_time=current,
                    details={
                        "source": source,
                        "venue_symbol": instrument.venue_symbol,
                        "timeframe": timeframe.value,
                        "open_time_ms": raw.open_time_ms,
                        "error": str(exc)[:500],
                    },
                )
            )
            logger.warning(
                "candle_quarantined",
                venue_symbol=instrument.venue_symbol,
                timeframe=timeframe.value,
                open_time_ms=raw.open_time_ms,
                error=str(exc)[:200],
            )
            continue
        if candle.close_time > current:
            continue  # in progress, not an anomaly
        candles.append(candle)
    return candles

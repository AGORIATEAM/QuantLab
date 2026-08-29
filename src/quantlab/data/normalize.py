"""RawKline → domain Candle normalization (03-Data-Engine §10, §26).

Pure functions, no I/O. Time convention: close_time = open_time + timeframe
duration (exclusive end), NOT the venue's inclusive …59.999 close — this keeps
QuantLab's [start, end) contract everywhere and stays deterministic.

Any inconsistency raises ValueError; the quarantine path in validate.py turns
that into a DataQualityEvent instead of a crash.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from quantlab.core.ids import new_id
from quantlab.data.binance.models import RawKline
from quantlab.domain.models import Candle, Timeframe

# Bump when the normalization rules change (03-Data-Engine §30); stored in
# candles.data_version so every row is traceable to the rules that shaped it.
NORMALIZATION_VERSION = "1.0"

_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


def from_epoch_ms(ms: int) -> datetime:
    """Exact ms-epoch → aware UTC datetime (no float round-trip)."""
    return _EPOCH + timedelta(milliseconds=ms)


def normalize_kline(
    raw: RawKline,
    instrument_id: uuid.UUID,
    timeframe: Timeframe,
    source: str,
) -> Candle:
    """Normalize one venue kline. Raises ValueError on any inconsistency:
    off-grid open time, close time not matching the timeframe, or a candle
    violating the OHLCV invariants enforced by the Candle model."""
    duration = timeframe.duration
    duration_ms = int(duration.total_seconds() * 1000)
    if raw.open_time_ms % duration_ms != 0:
        raise ValueError(
            f"open_time {raw.open_time_ms} is not aligned to the {timeframe.value} grid"
        )
    # Binance closes are inclusive: exactly open + duration - 1ms for a sane kline.
    expected_close_ms = raw.open_time_ms + duration_ms - 1
    if raw.close_time_ms != expected_close_ms:
        raise ValueError(
            f"close_time {raw.close_time_ms} does not match the {timeframe.value} timeframe "
            f"(expected {expected_close_ms})"
        )
    open_time = from_epoch_ms(raw.open_time_ms)
    return Candle(
        candle_id=new_id(),
        instrument_id=instrument_id,
        timeframe=timeframe,
        open_time=open_time,
        close_time=open_time + duration,
        open=raw.open,
        high=raw.high,
        low=raw.low,
        close=raw.close,
        volume=raw.volume,
        trade_count=raw.trade_count,
        source=source,
        data_version=NORMALIZATION_VERSION,
    )

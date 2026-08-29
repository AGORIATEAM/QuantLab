"""RawKline → Candle normalization: exact times, exact decimals, strict grid."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fixtures_binance import VALID_KLINE_ROW
from hypothesis import given
from hypothesis import strategies as st

from quantlab.core.ids import new_id
from quantlab.data.binance.models import RawKline
from quantlab.data.normalize import NORMALIZATION_VERSION, from_epoch_ms, normalize_kline
from quantlab.domain.models import Timeframe

RAW = RawKline.from_api(VALID_KLINE_ROW)


def test_normalize_valid_kline() -> None:
    instrument_id = new_id()
    candle = normalize_kline(RAW, instrument_id, Timeframe.M1, "binance")
    assert candle.open_time == datetime.fromtimestamp(1756166400, tz=UTC)
    # exclusive end: open + duration, not the venue's inclusive …59.999
    assert candle.close_time == candle.open_time + timedelta(minutes=1)
    assert str(candle.open) == "111544.83000000"
    assert str(candle.volume) == "5.70120000"
    assert candle.trade_count == 1234
    assert candle.instrument_id == instrument_id
    assert candle.source == "binance"
    assert candle.data_version == NORMALIZATION_VERSION


def test_off_grid_open_time_rejected() -> None:
    off = replace(RAW, open_time_ms=RAW.open_time_ms + 1, close_time_ms=RAW.close_time_ms + 1)
    with pytest.raises(ValueError, match="grid"):
        normalize_kline(off, new_id(), Timeframe.M1, "binance")


def test_close_time_not_matching_timeframe_rejected() -> None:
    bad = replace(RAW, close_time_ms=RAW.open_time_ms + 59_998)
    with pytest.raises(ValueError, match="does not match"):
        normalize_kline(bad, new_id(), Timeframe.M1, "binance")


def test_kline_normalized_under_wrong_timeframe_rejected() -> None:
    # a 1m kline pushed through as 5m: its close time betrays it
    with pytest.raises(ValueError, match="does not match"):
        normalize_kline(RAW, new_id(), Timeframe.M5, "binance")


def test_invalid_ohlc_rejected_by_domain_invariants() -> None:
    bad = replace(RAW, high=Decimal("1"), low=Decimal("2"))
    with pytest.raises(ValueError):
        normalize_kline(bad, new_id(), Timeframe.M1, "binance")


def test_from_epoch_ms_is_exact() -> None:
    expected = datetime.fromtimestamp(1756166459, tz=UTC) + timedelta(milliseconds=999)
    assert from_epoch_ms(1756166459999) == expected


@pytest.mark.parametrize(
    ("timeframe", "seconds"),
    [
        (Timeframe.M1, 60),
        (Timeframe.M3, 180),
        (Timeframe.M5, 300),
        (Timeframe.M15, 900),
        (Timeframe.M30, 1800),
        (Timeframe.H1, 3600),
        (Timeframe.H4, 14400),
        (Timeframe.D1, 86400),
    ],
)
def test_timeframe_durations(timeframe: Timeframe, seconds: int) -> None:
    assert timeframe.duration.total_seconds() == seconds


prices = st.decimals(
    min_value=Decimal("0.01"), max_value=Decimal("1000000"), allow_nan=False, places=8
)
volumes = st.decimals(min_value=0, max_value=Decimal("1000000"), allow_nan=False, places=8)


@given(open_=prices, close=prices, volume=volumes, step=st.integers(min_value=0, max_value=10**7))
def test_property_coherent_klines_always_normalize(
    open_: Decimal, close: Decimal, volume: Decimal, step: int
) -> None:
    open_ms = step * 60_000  # grid-aligned by construction
    raw = RawKline(
        open_time_ms=open_ms,
        open=open_,
        high=max(open_, close),
        low=min(open_, close),
        close=close,
        volume=volume,
        close_time_ms=open_ms + 59_999,
        quote_volume=volume,
        trade_count=1,
        taker_buy_base_volume=volume,
        taker_buy_quote_volume=volume,
    )
    candle = normalize_kline(raw, new_id(), Timeframe.M1, "test")
    assert candle.close_time - candle.open_time == timedelta(minutes=1)
    assert candle.low <= candle.open <= candle.high

"""Candle integrity invariants (18-Testing-Strategy §12: risk/domain logic first)."""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from quantlab.domain.models import Candle, Timeframe

OPEN_TIME = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)


def make_candle(**overrides: object) -> Candle:
    base: dict[str, object] = {
        "candle_id": uuid.uuid4(),
        "instrument_id": uuid.uuid4(),
        "timeframe": Timeframe.M5,
        "open_time": OPEN_TIME,
        "close_time": OPEN_TIME + timedelta(minutes=5),
        "open": Decimal("100"),
        "high": Decimal("110"),
        "low": Decimal("95"),
        "close": Decimal("105"),
        "volume": Decimal("12.5"),
        "source": "test",
    }
    base.update(overrides)
    return Candle(**base)  # type: ignore[arg-type]


def test_valid_candle() -> None:
    candle = make_candle()
    assert candle.high >= candle.low


@pytest.mark.parametrize(
    "overrides",
    [
        {"high": Decimal("99")},  # high < open
        {"high": Decimal("104"), "close": Decimal("105")},  # high < close
        {"low": Decimal("101")},  # low > open
        {"volume": Decimal("-1")},  # negative volume
        {"close_time": OPEN_TIME},  # close_time == open_time
    ],
)
def test_invalid_candles_rejected(overrides: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        make_candle(**overrides)


def test_naive_datetime_rejected() -> None:
    with pytest.raises(ValueError):
        make_candle(open_time=datetime(2026, 1, 1, 0, 0))


prices = st.decimals(
    min_value=Decimal("0.01"), max_value=Decimal("1000000"), allow_nan=False, places=2
)


@given(a=prices, b=prices, c=prices, d=prices)
def test_property_any_ohlc_ordering_is_normalizable(
    a: Decimal, b: Decimal, c: Decimal, d: Decimal
) -> None:
    """For any four prices, a candle built with high=max and low=min is valid."""
    values = [a, b, c, d]
    candle = make_candle(open=a, close=d, high=max(values), low=min(values))
    assert candle.low <= candle.open <= candle.high

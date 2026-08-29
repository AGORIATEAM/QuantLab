"""Quarantine path: invalid data → quality event, batch continues, no crash."""

from dataclasses import replace
from datetime import datetime
from decimal import Decimal

import pytest
from fakes import InMemoryQualityEvents
from fixtures_binance import SECOND_KLINE_ROW, VALID_KLINE_ROW

from quantlab.core.ids import new_id
from quantlab.data.binance.models import RawKline
from quantlab.data.normalize import from_epoch_ms
from quantlab.data.validate import normalize_and_validate
from quantlab.domain.models import Candle, Instrument, QualityCode, QualitySeverity, Timeframe

RAW_1 = RawKline.from_api(VALID_KLINE_ROW)  # open 1756166400000, closes at …460000
RAW_2 = RawKline.from_api(SECOND_KLINE_ROW)  # open 1756166460000, closes at …520000
AFTER_BOTH = from_epoch_ms(1756166600000)

INSTRUMENT = Instrument(
    instrument_id=new_id(),
    venue_id=new_id(),
    asset_id=None,
    venue_symbol="BTCUSDT",
    instrument_type="spot",
    tick_size=Decimal("0.01"),
    lot_size=Decimal("0.00001"),
)


def run(
    raws: list[RawKline], now: datetime = AFTER_BOTH
) -> tuple[list[Candle], InMemoryQualityEvents]:
    events = InMemoryQualityEvents()
    candles = normalize_and_validate(raws, INSTRUMENT, Timeframe.M1, "binance", events, now=now)
    return candles, events


def test_valid_batch_normalizes_in_order_without_events() -> None:
    candles, events = run([RAW_1, RAW_2])
    assert [c.open_time for c in candles] == [
        from_epoch_ms(1756166400000),
        from_epoch_ms(1756166460000),
    ]
    assert events.events == []


def test_invalid_kline_is_quarantined_and_batch_continues() -> None:
    bad = replace(RAW_1, high=Decimal("1"), low=Decimal("2"))
    candles, events = run([bad, RAW_2])

    assert [c.open_time for c in candles] == [from_epoch_ms(1756166460000)]
    assert len(events.events) == 1
    event = events.events[0]
    assert event.code is QualityCode.INVALID_CANDLE
    assert event.severity is QualitySeverity.ERROR
    assert event.instrument_id == INSTRUMENT.instrument_id
    assert event.details is not None
    assert event.details["open_time_ms"] == RAW_1.open_time_ms
    assert event.details["venue_symbol"] == "BTCUSDT"
    assert event.details["error"]


def test_in_progress_candle_is_excluded_without_event() -> None:
    # now falls inside RAW_2's minute: RAW_2 is not closed yet
    candles, events = run([RAW_1, RAW_2], now=from_epoch_ms(1756166480000))
    assert [c.open_time for c in candles] == [from_epoch_ms(1756166400000)]
    assert events.events == []


def test_candle_closing_exactly_now_is_kept() -> None:
    candles, _ = run([RAW_1], now=from_epoch_ms(1756166460000))
    assert len(candles) == 1


def test_naive_now_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        run([RAW_1], now=datetime(2026, 8, 26, 12, 0))


def test_empty_batch_returns_empty() -> None:
    candles, events = run([])
    assert candles == []
    assert events.events == []

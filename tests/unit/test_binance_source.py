"""BinanceCandleSource end to end: mocked venue → domain Candles + quarantine."""

from __future__ import annotations

import itertools
from decimal import Decimal

import httpx
from fakes import InMemoryQualityEvents
from fixtures_binance import KLINES_PAYLOAD, SECOND_KLINE_ROW, VALID_KLINE_ROW

from quantlab.core.ids import new_id
from quantlab.data.binance.client import BinanceRestClient
from quantlab.data.binance.source import SOURCE_BINANCE, BinanceCandleSource
from quantlab.data.normalize import from_epoch_ms
from quantlab.domain.models import Instrument, QualityCode, Timeframe

START = from_epoch_ms(1756166400000)
END = from_epoch_ms(1756166520000)
AFTER_BOTH_MS = 1756166600000

INSTRUMENT = Instrument(
    instrument_id=new_id(),
    venue_id=new_id(),
    asset_id=None,
    venue_symbol="BTCUSDT",
    instrument_type="spot",
    tick_size=Decimal("0.01"),
    lot_size=Decimal("0.00001"),
)


def make_source(
    handler: object, now_ms: int = AFTER_BOTH_MS
) -> tuple[BinanceCandleSource, InMemoryQualityEvents]:
    counter = itertools.count()
    client = BinanceRestClient(
        transport=httpx.MockTransport(handler),  # type: ignore[arg-type]
        sleep=lambda _s: None,
        monotonic=lambda: float(next(counter)),
    )
    events = InMemoryQualityEvents()
    return BinanceCandleSource(client, events, now=lambda: from_epoch_ms(now_ms)), events


def test_fetch_candles_returns_normalized_domain_candles() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=KLINES_PAYLOAD)

    source, events = make_source(handler)
    candles = source.fetch_candles(INSTRUMENT, Timeframe.M1, START, END)

    assert seen[0].url.params["symbol"] == "BTCUSDT"  # venue symbol from the instrument
    assert [c.open_time for c in candles] == [
        from_epoch_ms(1756166400000),
        from_epoch_ms(1756166460000),
    ]
    assert all(c.source == SOURCE_BINANCE for c in candles)
    assert all(c.instrument_id == INSTRUMENT.instrument_id for c in candles)
    assert events.events == []


def test_in_progress_tail_is_excluded() -> None:
    source, _ = make_source(
        lambda _r: httpx.Response(200, json=KLINES_PAYLOAD), now_ms=1756166480000
    )
    candles = source.fetch_candles(INSTRUMENT, Timeframe.M1, START, END)
    assert [c.open_time for c in candles] == [from_epoch_ms(1756166400000)]


def test_invalid_row_is_quarantined_not_fatal() -> None:
    bad_row = list(VALID_KLINE_ROW)
    bad_row[2] = "0.00000001"  # high far below open/close → domain invariant violation
    payload = [bad_row, SECOND_KLINE_ROW]

    source, events = make_source(lambda _r: httpx.Response(200, json=payload))
    candles = source.fetch_candles(INSTRUMENT, Timeframe.M1, START, END)

    assert [c.open_time for c in candles] == [from_epoch_ms(1756166460000)]
    assert [e.code for e in events.events] == [QualityCode.INVALID_CANDLE]


def test_health_check_delegates_to_client() -> None:
    source, _ = make_source(lambda _r: httpx.Response(200, json={}))
    assert source.health_check() is True

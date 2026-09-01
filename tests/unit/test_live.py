"""Live ingestion: WS parsing, closed-only archiving, idempotence,
outage reconciliation with true REST provenance."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fakes import (
    GridSource,
    InMemoryCandles,
    InMemoryQualityEvents,
    InMemoryRawWsMessages,
    RecordingAudit,
)

from quantlab.core.clock import SimulatedClock
from quantlab.core.ids import new_id
from quantlab.data.binance.ws import combined_stream_url, parse_ws_message, stream_name
from quantlab.data.errors import MalformedPayloadError
from quantlab.data.live import SOURCE_BINANCE_REST, SOURCE_BINANCE_WS, LiveIngestor
from quantlab.domain.models import Candle, Instrument, Timeframe

TF = Timeframe.M1
T0 = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)

INSTRUMENT = Instrument(
    instrument_id=new_id(),
    venue_id=new_id(),
    asset_id=None,
    venue_symbol="BTCUSDT",
    instrument_type="spot",
    tick_size=Decimal("0.01"),
    lot_size=Decimal("0.00001"),
)


def ws_frame(open_time: datetime, closed: bool = True, close: str = "100.5") -> str:
    open_ms = int(open_time.timestamp() * 1000)
    close_ms = open_ms + 59_999
    return json.dumps(
        {
            "stream": "btcusdt@kline_1m",
            "data": {
                "e": "kline",
                "E": close_ms + 150,  # venue event time: shortly after close
                "s": "BTCUSDT",
                "k": {
                    "t": open_ms,
                    "T": close_ms,
                    "s": "BTCUSDT",
                    "i": "1m",
                    "o": "100.0",
                    "h": "101.0",
                    "l": "99.0",
                    "c": close,
                    "v": "12.5",
                    "n": 42,
                    "x": closed,
                    "q": "1250.0",
                    "V": "6.0",
                    "Q": "600.0",
                },
            },
        }
    )


def make_ingestor(
    candles: InMemoryCandles | None = None,
    now: datetime | None = None,
) -> tuple[LiveIngestor, InMemoryCandles, InMemoryQualityEvents, InMemoryRawWsMessages]:
    candles = candles or InMemoryCandles()
    quality = InMemoryQualityEvents()
    raw = InMemoryRawWsMessages()
    ingestor = LiveIngestor(
        candles=candles,
        quality=quality,
        raw_messages=raw,
        instruments={"BTCUSDT": INSTRUMENT},
        timeframes=[TF],
        clock=SimulatedClock(now or T0 + TF.duration),
    )
    return ingestor, candles, quality, raw


def test_stream_helpers() -> None:
    assert stream_name("BTCUSDT", Timeframe.H1) == "btcusdt@kline_1h"
    url = combined_stream_url(["a@kline_1m", "b@kline_1h"])
    assert url.endswith("?streams=a@kline_1m/b@kline_1h")
    with pytest.raises(ValueError):
        combined_stream_url([])


def test_parse_ws_message_closed_and_open() -> None:
    closed = parse_ws_message(ws_frame(T0, closed=True))
    assert closed is not None and closed.closed
    assert closed.venue_symbol == "BTCUSDT"
    assert closed.timeframe is TF
    assert closed.kline.close == Decimal("100.5")

    update = parse_ws_message(ws_frame(T0, closed=False))
    assert update is not None and not update.closed

    assert parse_ws_message(json.dumps({"result": None, "id": 1})) is None  # sub ack
    with pytest.raises(MalformedPayloadError):
        parse_ws_message(json.dumps({"stream": "x", "data": {"e": "kline", "k": {}}}))


def test_closed_kline_is_archived_and_inserted_as_binance_ws() -> None:
    ingestor, candles, _quality, raw = make_ingestor()
    ingestor.process_frame(ws_frame(T0))

    assert len(raw.rows) == 1
    assert raw.rows[0][2] == "btcusdt@kline_1m"
    stored = list(candles.rows.values())
    assert len(stored) == 1
    assert stored[0].source == SOURCE_BINANCE_WS
    assert stored[0].open_time == T0
    assert ingestor.stats.inserted == 1
    assert ingestor.stats.last_latency_ms is not None


def test_intra_candle_update_is_ignored_and_not_archived() -> None:
    ingestor, candles, _quality, raw = make_ingestor()
    ingestor.process_frame(ws_frame(T0, closed=False))

    assert raw.rows == []
    assert candles.rows == {}
    assert ingestor.stats.closed_klines == 0


def test_duplicate_closed_kline_journaled_twice_inserted_once() -> None:
    ingestor, candles, _quality, raw = make_ingestor()
    ingestor.process_frame(ws_frame(T0))
    ingestor.process_frame(ws_frame(T0))  # venue re-push after reconnect

    assert len(raw.rows) == 2  # the raw journal keeps everything (A.2)
    assert len(candles.rows) == 1  # the candle path is idempotent
    assert ingestor.stats.duplicates == 1


def test_malformed_frame_counted_not_fatal() -> None:
    ingestor, candles, _quality, raw = make_ingestor()
    ingestor.process_frame('{"stream": "x", "data": {"e": "kline", "k": {"t": "bad"}}}')
    assert ingestor.stats.malformed == 1
    assert raw.rows == [] and candles.rows == {}


def test_reconcile_records_outage_and_backfills_with_rest_provenance() -> None:
    def ws_candle(open_time: datetime) -> Candle:
        return Candle(
            candle_id=new_id(),
            instrument_id=INSTRUMENT.instrument_id,
            timeframe=TF,
            open_time=open_time,
            close_time=open_time + TF.duration,
            open=Decimal("100"),
            high=Decimal("101"),
            low=Decimal("99"),
            close=Decimal("100.5"),
            volume=Decimal("1"),
            source=SOURCE_BINANCE_WS,
        )

    def rest_candle(open_time: datetime) -> Candle:
        return ws_candle(open_time).model_copy(
            update={"candle_id": new_id(), "source": SOURCE_BINANCE_REST}
        )

    candles = InMemoryCandles()
    candles.insert_many([ws_candle(T0)])  # WS series stops at T0, then outage
    now = T0 + 5 * TF.duration  # 4 candles missed
    ingestor, candles, quality, _raw = make_ingestor(candles=candles, now=now)
    venue_rest = GridSource([rest_candle(T0 + i * TF.duration) for i in range(1, 5)])
    audit = RecordingAudit()

    ingestor.reconcile(venue_rest, audit)

    outages = quality.list_unresolved(INSTRUMENT.instrument_id)
    assert [e.code.value for e in outages] == ["WS_OUTAGE"]
    details = outages[0].details
    assert details is not None
    assert details["expected_candles"] == 4
    assert details["gap_start"] == (T0 + TF.duration).isoformat()
    # missed candles landed under their TRUE provenance
    rest_rows = [c for c in candles.rows.values() if c.source == SOURCE_BINANCE_REST]
    ws_rows = [c for c in candles.rows.values() if c.source == SOURCE_BINANCE_WS]
    assert len(rest_rows) == 4
    assert len(ws_rows) == 1  # the WS series keeps its hole
    assert ingestor.stats.reconciled == 4
    assert ingestor.stats.outages == 1


def test_reconcile_noop_without_prior_ws_data_or_gap() -> None:
    ingestor, _candles, quality, _raw = make_ingestor()
    ingestor.reconcile(GridSource([]), RecordingAudit())
    assert quality.events == []  # first connection: series starts now
    assert ingestor.stats.outages == 0

"""Migration 0005 against real PostgreSQL: raw journal append-only, and the
candles_canonical view's REST-over-WS precedence."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import psycopg
import pytest

from quantlab.core.ids import new_id
from quantlab.core.timeutils import utc_now
from quantlab.domain.models import Candle, Timeframe
from quantlab.storage.postgres.adapter import (
    PostgresCandleRepository,
    PostgresRawWsMessageWriter,
)

TF = Timeframe.H1
# 2032: outside every other integration test's insert window (shared DB).
T0 = datetime(2032, 1, 1, 0, 0, tzinfo=UTC)


def make_candle(instrument_id: uuid.UUID, open_time: datetime, source: str, close: str) -> Candle:
    return Candle(
        candle_id=new_id(),
        instrument_id=instrument_id,
        timeframe=TF,
        open_time=open_time,
        close_time=open_time + TF.duration,
        open=Decimal("100"),
        high=Decimal("500"),
        low=Decimal("50"),
        close=Decimal(close),
        volume=Decimal("1"),
        source=source,
    )


def test_raw_ws_messages_is_append_only(database_url: str) -> None:
    writer = PostgresRawWsMessageWriter(database_url)
    message_id = new_id()
    writer.insert(message_id, utc_now(), "btcusdt@kline_1m", {"k": {"x": True}})

    with psycopg.connect(database_url) as conn, conn.cursor() as cur:
        with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
            cur.execute(
                "UPDATE raw_ws_messages SET stream = 'tampered' WHERE message_id = %s",
                (message_id,),
            )
        conn.rollback()
        with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
            cur.execute("DELETE FROM raw_ws_messages WHERE message_id = %s", (message_id,))
        conn.rollback()
        # no deduplication: the same payload can be journaled again (A.2)
        writer.insert(new_id(), utc_now(), "btcusdt@kline_1m", {"k": {"x": True}})
        cur.execute("SELECT count(*) FROM raw_ws_messages WHERE stream = 'btcusdt@kline_1m'")
        row = cur.fetchone()
        assert row is not None and row[0] == 2


def test_candles_canonical_prefers_rest_over_ws(
    database_url: str, btc_instrument_id: uuid.UUID
) -> None:
    candles = PostgresCandleRepository(database_url)
    # hour 0: both sources -> the view must expose the REST row
    candles.insert_many(
        [
            make_candle(btc_instrument_id, T0, "binance", close="111"),
            make_candle(btc_instrument_id, T0, "binance_ws", close="222"),
        ]
    )
    # hour 1: WS only -> visible through the view (continuity)
    candles.insert_many([make_candle(btc_instrument_id, T0 + TF.duration, "binance_ws", "333")])

    with psycopg.connect(database_url) as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT open_time, source, close FROM candles_canonical
            WHERE instrument_id = %s AND timeframe = %s AND open_time >= %s
            ORDER BY open_time
            """,
            (btc_instrument_id, TF.value, T0),
        )
        rows = cur.fetchall()
    assert [(r[1], r[2]) for r in rows] == [
        ("binance", Decimal("111")),
        ("binance_ws", Decimal("333")),
    ]


def test_latency_stats_from_raw_journal(database_url: str) -> None:
    writer = PostgresRawWsMessageWriter(database_url)
    base = utc_now()
    # three messages with venue event times 100/200/700 ms before reception
    for offset_ms in (100, 200, 700):
        received = base
        event_ms = int(received.timestamp() * 1000) - offset_ms
        writer.insert(new_id(), received, "latency@test", {"data": {"e": "kline", "E": event_ms}})
    stats = writer.latency_stats(base - timedelta(minutes=1))
    assert stats is not None
    avg, p95, mx, count = stats
    assert count >= 3
    assert mx >= 700
    assert avg > 0 and p95 <= mx

    assert writer.latency_stats(base + timedelta(hours=1)) is None

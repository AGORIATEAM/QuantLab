"""Replay against real PostgreSQL: REPEATABLE READ snapshot isolation,
fail-closed refusal after tampering, candles append-only trigger (0004)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import psycopg
import pytest

from quantlab.core.clock import SimulatedClock
from quantlab.core.ids import new_id
from quantlab.data.datasets import SeriesResolver, freeze_dataset
from quantlab.data.replay import ReplayIntegrityError, replay_candles
from quantlab.domain.models import Candle, Timeframe
from quantlab.storage.postgres.adapter import (
    PostgresAuditEventWriter,
    PostgresCandleRepository,
    PostgresCandleSnapshotFactory,
    PostgresDataQualityEventRepository,
    PostgresDatasetRepository,
    PostgresInstrumentRepository,
    PostgresVenueRepository,
)

TF = Timeframe.H1
# 2031: outside every other integration test's insert window (shared DB).
T0 = datetime(2031, 1, 1, 0, 0, tzinfo=UTC)
SOURCE = "binance"


def make_candle(instrument_id: uuid.UUID, open_time: datetime) -> Candle:
    return Candle(
        candle_id=new_id(),
        instrument_id=instrument_id,
        timeframe=TF,
        open_time=open_time,
        close_time=open_time + TF.duration,
        open=Decimal("100"),
        high=Decimal("101"),
        low=Decimal("99"),
        close=Decimal("100.5"),
        volume=Decimal("1"),
        trade_count=3,
        source=SOURCE,
    )


def hour(i: int) -> datetime:
    return T0 + i * TF.duration


def test_replay_streams_under_snapshot_and_then_refuses(
    database_url: str, btc_instrument_id: uuid.UUID
) -> None:
    candles = PostgresCandleRepository(database_url)
    datasets = PostgresDatasetRepository(database_url)
    quality = PostgresDataQualityEventRepository(database_url)
    audit = PostgresAuditEventWriter(database_url)
    resolve = SeriesResolver(
        PostgresVenueRepository(database_url), PostgresInstrumentRepository(database_url)
    )
    venue = PostgresVenueRepository(database_url).get_by_code("BINANCE")
    instrument = PostgresInstrumentRepository(database_url).get(btc_instrument_id)
    assert venue is not None and instrument is not None

    candles.insert_many([make_candle(btc_instrument_id, hour(i)) for i in range(6)])
    freeze_dataset(
        candles, datasets, audit, "rp-it", "v1", [(venue, instrument)], [TF], T0, hour(6), SOURCE
    )

    # Amendement 2: an insert landing while the replay is running is invisible
    # to its REPEATABLE READ snapshot — the stream is unchanged.
    clock = SimulatedClock(T0)
    stream = replay_candles(
        PostgresCandleSnapshotFactory(database_url),
        datasets,
        resolve,
        quality,
        audit,
        "rp-it",
        "v1",
        clock,
    )
    first = [next(stream) for _ in range(2)]
    candles.insert_many(
        [make_candle(btc_instrument_id, hour(2) + timedelta(minutes=30))]  # inside the range
    )
    rest = list(stream)
    assert len(first) + len(rest) == 6
    assert clock.now() == hour(6)

    # Fail-closed: a fresh replay sees the diverged store and refuses.
    with pytest.raises(ReplayIntegrityError, match="diverged"):
        list(
            replay_candles(
                PostgresCandleSnapshotFactory(database_url),
                datasets,
                resolve,
                quality,
                audit,
                "rp-it",
                "v1",
                SimulatedClock(T0),
            )
        )


def test_candles_table_is_append_only(database_url: str, btc_instrument_id: uuid.UUID) -> None:
    candles = PostgresCandleRepository(database_url)
    candles.insert_many([make_candle(btc_instrument_id, hour(100))])
    with psycopg.connect(database_url) as conn, conn.cursor() as cur:
        with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
            cur.execute(
                "UPDATE candles SET close = 1 WHERE instrument_id = %s AND open_time = %s",
                (btc_instrument_id, hour(100)),
            )
        conn.rollback()
        with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
            cur.execute(
                "DELETE FROM candles WHERE instrument_id = %s AND open_time = %s",
                (btc_instrument_id, hour(100)),
            )
        conn.rollback()


def test_snapshot_repository_is_read_only(database_url: str, btc_instrument_id: uuid.UUID) -> None:
    factory = PostgresCandleSnapshotFactory(database_url)
    with factory() as snapshot:
        with pytest.raises(RuntimeError, match="read-only"):
            snapshot.insert_many([make_candle(btc_instrument_id, hour(200))])

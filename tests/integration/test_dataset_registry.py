"""Dataset registry against real PostgreSQL: migration 0003, immutability,
freeze/verify round-trip, and the late-insertion failure required by T6."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import psycopg
import pytest

from quantlab.core.ids import new_id
from quantlab.data.datasets import SeriesResolver, freeze_dataset, verify_dataset
from quantlab.domain.models import Candle, QualityCode, Timeframe
from quantlab.storage.postgres.adapter import (
    PostgresAuditEventWriter,
    PostgresCandleRepository,
    PostgresDataQualityEventRepository,
    PostgresDatasetRepository,
    PostgresInstrumentRepository,
    PostgresVenueRepository,
)

TF = Timeframe.H1
# 2030: far from every other integration test's candle inserts — the session
# database is shared and (instrument, tf, open_time, source) must not collide.
T0 = datetime(2030, 1, 1, 0, 0, tzinfo=UTC)
SOURCE = "binance"


def make_candle(instrument_id: uuid.UUID, open_time: datetime) -> Candle:
    return Candle(
        candle_id=new_id(),
        instrument_id=instrument_id,
        timeframe=TF,
        open_time=open_time,
        close_time=open_time + TF.duration,
        open=Decimal("100.50"),
        high=Decimal("101.00"),
        low=Decimal("99.999"),
        close=Decimal("100.5"),
        volume=Decimal("1.10"),
        trade_count=7,
        source=SOURCE,
    )


def hour(i: int) -> datetime:
    return T0 + i * TF.duration


def test_freeze_verify_and_late_insertion(database_url: str, btc_instrument_id: uuid.UUID) -> None:
    candles = PostgresCandleRepository(database_url)
    datasets = PostgresDatasetRepository(database_url)
    quality = PostgresDataQualityEventRepository(database_url)
    audit = PostgresAuditEventWriter(database_url)
    venues = PostgresVenueRepository(database_url)
    instruments = PostgresInstrumentRepository(database_url)
    resolve = SeriesResolver(venues, instruments)

    venue = venues.get_by_code("BINANCE")
    assert venue is not None
    instrument = instruments.get(btc_instrument_id)
    assert instrument is not None

    candles.insert_many([make_candle(btc_instrument_id, hour(i)) for i in range(3)])
    dataset = freeze_dataset(
        candles,
        datasets,
        audit,
        "it-dataset",
        "v1",
        [(venue, instrument)],
        [TF],
        T0,
        hour(3),
        SOURCE,
        code_commit="deadbeef",
    )

    # round-trip through the table preserves everything
    stored = datasets.get("it-dataset", "v1")
    assert stored is not None
    assert stored.content_hash == dataset.content_hash
    assert stored.metadata is not None
    assert stored.metadata["series"][0]["candle_count"] == 3

    report = verify_dataset(candles, datasets, resolve, quality, audit, "it-dataset", "v1")
    assert report.ok

    # T6 acceptance: a late insertion inside the frozen range must fail verify
    candles.insert_many([make_candle(btc_instrument_id, hour(1) + TF.duration / 2)])
    report = verify_dataset(candles, datasets, resolve, quality, audit, "it-dataset", "v1")
    assert not report.ok
    assert report.mismatches[0].kind == "count"
    mismatch_events = quality.list_unresolved(code=QualityCode.CANDLE_MISMATCH)
    assert any(
        e.details is not None and e.details.get("dataset_name") == "it-dataset"
        for e in mismatch_events
    )


def test_datasets_table_is_append_only_and_unique(database_url: str) -> None:
    with psycopg.connect(database_url) as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO datasets (dataset_id, dataset_name, version, storage_uri,
                                  content_hash, source, status)
            VALUES (%s, 'immut', 'v1', 'postgresql://x', 'h', 'binance', 'published')
            """,
            (new_id(),),
        )
        conn.commit()

        with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
            cur.execute(
                "UPDATE datasets SET content_hash = 'tampered' WHERE dataset_name = 'immut'"
            )
        conn.rollback()
        with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
            cur.execute("DELETE FROM datasets WHERE dataset_name = 'immut'")
        conn.rollback()
        with pytest.raises(psycopg.errors.UniqueViolation):
            cur.execute(
                """
                INSERT INTO datasets (dataset_id, dataset_name, version, storage_uri,
                                      content_hash, source, status)
                VALUES (%s, 'immut', 'v1', 'postgresql://x', 'h2', 'binance', 'published')
                """,
                (new_id(),),
            )
        conn.rollback()
        with pytest.raises(psycopg.errors.CheckViolation):
            cur.execute(
                """
                INSERT INTO datasets (dataset_id, dataset_name, version, storage_uri,
                                      content_hash, source, status)
                VALUES (%s, 'drafty', 'v1', 'postgresql://x', 'h', 'binance', 'draft')
                """,
                (new_id(),),
            )
        conn.rollback()


def test_stream_candle_rows_matches_read_range(
    database_url: str, btc_instrument_id: uuid.UUID
) -> None:
    candles = PostgresCandleRepository(database_url)
    start, end = hour(10), hour(15)
    candles.insert_many([make_candle(btc_instrument_id, hour(i)) for i in range(10, 15)])

    streamed = [
        row
        for batch in candles.stream_candle_rows(
            btc_instrument_id, TF, SOURCE, start, end, batch_size=2
        )
        for row in batch
    ]
    read = candles.read_range(btc_instrument_id, TF, start, end)

    assert candles.count_range(btc_instrument_id, TF, SOURCE, start, end) == 5
    assert [r[0] for r in streamed] == [c.open_time for c in read]
    assert [r[4] for r in streamed] == [c.close for c in read]

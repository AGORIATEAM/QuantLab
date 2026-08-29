"""Batch candle insertion and resumable download against a real database (T4)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import psycopg
import pytest

from quantlab.core.ids import new_id
from quantlab.data.download import download_history
from quantlab.domain.models import Candle, Instrument, Timeframe
from quantlab.storage.postgres.adapter import (
    PostgresAuditEventWriter,
    PostgresCandleRepository,
    PostgresInstrumentRepository,
    PostgresVenueRepository,
)

pytestmark = pytest.mark.integration

TF = Timeframe.M1
T0 = datetime(2026, 7, 1, 0, 0, tzinfo=UTC)


def make_candle(instrument_id: uuid.UUID, index: int, source: str) -> Candle:
    open_time = T0 + index * TF.duration
    return Candle(
        candle_id=new_id(),
        instrument_id=instrument_id,
        timeframe=TF,
        open_time=open_time,
        close_time=open_time + TF.duration,
        open=Decimal("100.00000001"),
        high=Decimal("101"),
        low=Decimal("99"),
        close=Decimal("100.5"),
        volume=Decimal("1.23456789"),
        trade_count=42,
        source=source,
    )


class GridSource:
    """Deterministic candle source (no live API in tests, docs/17 §77)."""

    def __init__(self, instrument_id: uuid.UUID, count: int, source: str) -> None:
        self.candles = [make_candle(instrument_id, i, source) for i in range(count)]
        self.calls = 0

    def fetch_candles(
        self,
        instrument: Instrument,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
        limit: int = 1000,
    ) -> list[Candle]:
        self.calls += 1
        return [c for c in self.candles if start <= c.open_time < end][:limit]

    def health_check(self) -> bool:
        return True


def test_batch_insert_is_idempotent_and_counts_only_new_rows(
    database_url: str, btc_instrument_id: uuid.UUID
) -> None:
    repo = PostgresCandleRepository(database_url)
    source = "it_batch"
    candles = [make_candle(btc_instrument_id, i, source) for i in range(500)]

    assert repo.insert_many(candles) == 500
    assert repo.insert_many(candles) == 0  # ON CONFLICT DO NOTHING, immutability kept
    # overlapping batch: only the 100 new rows count
    more = candles[400:] + [make_candle(btc_instrument_id, 500 + i, source) for i in range(100)]
    assert repo.insert_many(more) == 100

    assert repo.latest_open_time(btc_instrument_id, TF, source) == T0 + 599 * TF.duration
    assert repo.latest_open_time(btc_instrument_id, TF, "other_source") is None


def test_download_resumes_and_rerun_inserts_nothing(
    database_url: str, btc_instrument_id: uuid.UUID
) -> None:
    source_name = "it_download"
    instrument_repo = PostgresInstrumentRepository(database_url)
    venue = PostgresVenueRepository(database_url).get_by_code("BINANCE")
    assert venue is not None
    instrument = instrument_repo.get_by_venue_symbol(venue.venue_id, "ETHUSDT")
    assert instrument is not None

    candles_repo = PostgresCandleRepository(database_url)
    audit = PostgresAuditEventWriter(database_url)
    grid = GridSource(instrument.instrument_id, 250, source_name)
    end = T0 + 250 * TF.duration

    first = download_history(
        grid, candles_repo, audit, instrument, TF, T0, end, source_name, limit=100
    )
    assert (first.batches, first.inserted, first.duplicates_skipped) == (3, 250, 0)

    rerun = download_history(
        grid, candles_repo, audit, instrument, TF, T0, end, source_name, limit=100
    )
    assert rerun.inserted == 0
    assert rerun.fetched == 0  # checkpoint made the range empty: zero venue calls
    assert rerun.resumed_from == T0 + 249 * TF.duration

    stored = candles_repo.read_range(instrument.instrument_id, TF, T0, end)
    assert len([c for c in stored if c.source == source_name]) == 250

    with psycopg.connect(database_url) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT action FROM audit_events "
            "WHERE actor_id = 'download_history' ORDER BY event_time"
        )
        actions = [r[0] for r in cur.fetchall()]
    assert actions.count("HISTORICAL_DOWNLOAD_COMPLETED") == 2

"""PostgreSQL adapters implementing the repository interfaces.

Phase 0 scope: enough to seed reference data, persist candles immutably and
write audit events. Extended in Phase 1 (Data Platform).
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import datetime
from typing import Any

import psycopg

from quantlab.audit.events import AuditEvent
from quantlab.core.ids import new_id
from quantlab.domain.models import (
    Candle,
    DataQualityEvent,
    Dataset,
    Instrument,
    InstrumentStatus,
    QualityCode,
    QualitySeverity,
    Timeframe,
    Venue,
)
from quantlab.storage.repositories import CandleRow


class PostgresVenueRepository:
    def __init__(self, conninfo: str) -> None:
        self._conninfo = conninfo

    def get_by_code(self, code: str) -> Venue | None:
        query = "SELECT venue_id, code, name, venue_type, is_active FROM venues WHERE code = %s"
        with psycopg.connect(self._conninfo) as conn, conn.cursor() as cur:
            cur.execute(query, (code,))
            row = cur.fetchone()
        if row is None:
            return None
        return Venue(venue_id=row[0], code=row[1], name=row[2], venue_type=row[3], is_active=row[4])

    def insert(self, venue: Venue) -> None:
        query = """
            INSERT INTO venues (venue_id, code, name, venue_type, is_active)
            VALUES (%s, %s, %s, %s, %s)
        """
        with psycopg.connect(self._conninfo) as conn, conn.cursor() as cur:
            cur.execute(
                query, (venue.venue_id, venue.code, venue.name, venue.venue_type, venue.is_active)
            )
            conn.commit()


_INSTRUMENT_COLUMNS = """
    instrument_id, venue_id, asset_id, venue_symbol, instrument_type,
    tick_size, lot_size, min_quantity, min_notional, status
"""


def _row_to_instrument(row: tuple[Any, ...]) -> Instrument:
    return Instrument(
        instrument_id=row[0],
        venue_id=row[1],
        asset_id=row[2],
        venue_symbol=row[3],
        instrument_type=row[4],
        tick_size=row[5],
        lot_size=row[6],
        min_quantity=row[7],
        min_notional=row[8],
        status=InstrumentStatus(row[9]),
    )


class PostgresInstrumentRepository:
    def __init__(self, conninfo: str) -> None:
        self._conninfo = conninfo

    def get(self, instrument_id: uuid.UUID) -> Instrument | None:
        query = f"SELECT {_INSTRUMENT_COLUMNS} FROM instruments WHERE instrument_id = %s"
        with psycopg.connect(self._conninfo) as conn, conn.cursor() as cur:
            cur.execute(query, (instrument_id,))
            row = cur.fetchone()
        return None if row is None else _row_to_instrument(row)

    def get_by_venue_symbol(self, venue_id: uuid.UUID, venue_symbol: str) -> Instrument | None:
        query = (
            f"SELECT {_INSTRUMENT_COLUMNS} FROM instruments "
            "WHERE venue_id = %s AND venue_symbol = %s"
        )
        with psycopg.connect(self._conninfo) as conn, conn.cursor() as cur:
            cur.execute(query, (venue_id, venue_symbol))
            row = cur.fetchone()
        return None if row is None else _row_to_instrument(row)

    def insert(self, instrument: Instrument) -> None:
        query = f"""
            INSERT INTO instruments ({_INSTRUMENT_COLUMNS})
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        with psycopg.connect(self._conninfo) as conn, conn.cursor() as cur:
            cur.execute(
                query,
                (
                    instrument.instrument_id,
                    instrument.venue_id,
                    instrument.asset_id,
                    instrument.venue_symbol,
                    instrument.instrument_type,
                    instrument.tick_size,
                    instrument.lot_size,
                    instrument.min_quantity,
                    instrument.min_notional,
                    instrument.status.value,
                ),
            )
            conn.commit()


class PostgresCandleRepository:
    """Candle store adapter. With `connection`, every method runs on that
    shared connection/transaction (the snapshot path — read-only); otherwise
    each call opens its own connection."""

    def __init__(
        self, conninfo: str = "", *, connection: psycopg.Connection[Any] | None = None
    ) -> None:
        if not conninfo and connection is None:
            raise ValueError("either conninfo or connection is required")
        self._conninfo = conninfo
        self._connection = connection

    @contextmanager
    def _conn(self) -> Iterator[psycopg.Connection[Any]]:
        if self._connection is not None:
            yield self._connection
        else:
            with psycopg.connect(self._conninfo) as conn:
                yield conn

    def insert_many(self, candles: Sequence[Candle]) -> int:
        if self._connection is not None:
            raise RuntimeError("snapshot repository is read-only")
        if not candles:
            return 0
        query = """
            INSERT INTO candles (
                candle_id, instrument_id, timeframe, open_time, close_time,
                open, high, low, close, volume, trade_count, source, data_version
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (instrument_id, timeframe, open_time, source) DO NOTHING
        """
        rows = [
            (
                c.candle_id,
                c.instrument_id,
                c.timeframe.value,
                c.open_time,
                c.close_time,
                c.open,
                c.high,
                c.low,
                c.close,
                c.volume,
                c.trade_count,
                c.source,
                c.data_version,
            )
            for c in candles
        ]
        # executemany is pipelined in psycopg3 (04-Storage §27: batch, one
        # transaction); rowcount is the cumulated number of inserted rows,
        # so duplicates skipped by ON CONFLICT are not counted.
        with psycopg.connect(self._conninfo) as conn, conn.cursor() as cur:
            cur.executemany(query, rows)
            inserted = cur.rowcount
            conn.commit()
        return inserted

    def latest_open_time(
        self,
        instrument_id: uuid.UUID,
        timeframe: Timeframe,
        source: str,
    ) -> datetime | None:
        query = """
            SELECT MAX(open_time) FROM candles
            WHERE instrument_id = %s AND timeframe = %s AND source = %s
        """
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(query, (instrument_id, timeframe.value, source))
            row = cur.fetchone()
        return row[0] if row is not None else None

    def count_range(
        self,
        instrument_id: uuid.UUID,
        timeframe: Timeframe,
        source: str,
        start: datetime,
        end: datetime,
    ) -> int:
        query = """
            SELECT count(*) FROM candles
            WHERE instrument_id = %s AND timeframe = %s AND source = %s
              AND open_time >= %s AND open_time < %s
        """
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(query, (instrument_id, timeframe.value, source, start, end))
            row = cur.fetchone()
        return int(row[0]) if row is not None else 0

    def stream_candle_rows(
        self,
        instrument_id: uuid.UUID,
        timeframe: Timeframe,
        source: str,
        start: datetime,
        end: datetime,
        batch_size: int = 50_000,
    ) -> Iterator[Sequence[CandleRow]]:
        query = """
            SELECT open_time, open, high, low, close, volume, trade_count
            FROM candles
            WHERE instrument_id = %s AND timeframe = %s AND source = %s
              AND open_time >= %s AND open_time < %s
            ORDER BY open_time ASC
        """
        # Named cursor = server-side: rows travel in batches, never all at once.
        with self._conn() as conn:
            with conn.cursor(name=f"candle_stream_{new_id().hex}") as cur:
                cur.execute(query, (instrument_id, timeframe.value, source, start, end))
                while True:
                    rows = cur.fetchmany(batch_size)
                    if not rows:
                        break
                    yield rows

    def stream_candles(
        self,
        instrument_id: uuid.UUID,
        timeframe: Timeframe,
        source: str,
        start: datetime,
        end: datetime,
        batch_size: int = 50_000,
    ) -> Iterator[Sequence[Candle]]:
        query = """
            SELECT candle_id, instrument_id, timeframe, open_time, close_time,
                   open, high, low, close, volume, trade_count, source, data_version
            FROM candles
            WHERE instrument_id = %s AND timeframe = %s AND source = %s
              AND open_time >= %s AND open_time < %s
            ORDER BY open_time ASC
        """
        tf = timeframe  # single Timeframe object reused for every row
        with self._conn() as conn:
            with conn.cursor(name=f"candle_full_stream_{new_id().hex}") as cur:
                cur.execute(query, (instrument_id, timeframe.value, source, start, end))
                while True:
                    rows = cur.fetchmany(batch_size)
                    if not rows:
                        break
                    # model_construct skips pydantic validation: these rows
                    # come from a CHECK-constrained store that is hash-verified
                    # at replay startup; re-validating millions of candles is
                    # pure cost (T7).
                    yield [
                        Candle.model_construct(
                            candle_id=r[0],
                            instrument_id=r[1],
                            timeframe=tf,
                            open_time=r[3],
                            close_time=r[4],
                            open=r[5],
                            high=r[6],
                            low=r[7],
                            close=r[8],
                            volume=r[9],
                            trade_count=r[10],
                            source=r[11],
                            data_version=r[12],
                        )
                        for r in rows
                    ]

    def missing_ranges(
        self,
        instrument_id: uuid.UUID,
        timeframe: Timeframe,
        source: str,
        start: datetime,
        end: datetime,
    ) -> list[tuple[datetime, datetime]]:
        # Interior holes via a window function (one index scan, no
        # generate_series over millions of expected rows); leading and
        # trailing holes derived from MIN/MAX in Python.
        interior_query = """
            WITH stored AS (
                SELECT open_time,
                       LEAD(open_time) OVER (ORDER BY open_time) AS next_open
                FROM candles
                WHERE instrument_id = %(instrument_id)s AND timeframe = %(timeframe)s
                  AND source = %(source)s
                  AND open_time >= %(start)s AND open_time < %(end)s
            )
            SELECT open_time + %(step)s, next_open
            FROM stored
            WHERE next_open > open_time + %(step)s
            ORDER BY 1
        """
        bounds_query = """
            SELECT MIN(open_time), MAX(open_time) FROM candles
            WHERE instrument_id = %s AND timeframe = %s AND source = %s
              AND open_time >= %s AND open_time < %s
        """
        step = timeframe.duration
        params = {
            "instrument_id": instrument_id,
            "timeframe": timeframe.value,
            "source": source,
            "start": start,
            "end": end,
            "step": step,
        }
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(interior_query, params)
            interior = [(r[0], r[1]) for r in cur.fetchall()]
            cur.execute(bounds_query, (instrument_id, timeframe.value, source, start, end))
            first, last = cur.fetchone()  # type: ignore[misc]
        if first is None:
            return [(start, end)]
        holes: list[tuple[datetime, datetime]] = []
        if first > start:
            holes.append((start, first))
        holes.extend(interior)
        if last + step < end:
            holes.append((last + step, end))
        return holes

    def read_range(
        self,
        instrument_id: uuid.UUID,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
    ) -> list[Candle]:
        query = """
            SELECT candle_id, instrument_id, timeframe, open_time, close_time,
                   open, high, low, close, volume, trade_count, source, data_version
            FROM candles
            WHERE instrument_id = %s AND timeframe = %s
              AND open_time >= %s AND open_time < %s
            ORDER BY open_time ASC
        """
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(query, (instrument_id, timeframe.value, start, end))
            rows = cur.fetchall()
        return [
            Candle(
                candle_id=r[0],
                instrument_id=r[1],
                timeframe=Timeframe(r[2]),
                open_time=r[3],
                close_time=r[4],
                open=r[5],
                high=r[6],
                low=r[7],
                close=r[8],
                volume=r[9],
                trade_count=r[10],
                source=r[11],
                data_version=r[12],
            )
            for r in rows
        ]


class PostgresDataQualityEventRepository:
    def __init__(self, conninfo: str) -> None:
        self._conninfo = conninfo

    def insert(self, event: DataQualityEvent) -> None:
        query = """
            INSERT INTO data_quality_events (
                event_id, dataset_type, instrument_id, severity, code,
                event_time, details, resolved_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        with psycopg.connect(self._conninfo) as conn, conn.cursor() as cur:
            cur.execute(
                query,
                (
                    event.event_id,
                    event.dataset_type,
                    event.instrument_id,
                    event.severity.value,
                    event.code.value,
                    event.event_time,
                    json.dumps(event.details) if event.details is not None else None,
                    event.resolved_at,
                ),
            )
            conn.commit()

    def list_unresolved(
        self,
        instrument_id: uuid.UUID | None = None,
        code: QualityCode | None = None,
    ) -> list[DataQualityEvent]:
        query = """
            SELECT event_id, dataset_type, instrument_id, severity, code,
                   event_time, details, resolved_at
            FROM data_quality_events
            WHERE resolved_at IS NULL
              AND (%(instrument_id)s::uuid IS NULL OR instrument_id = %(instrument_id)s)
              AND (%(code)s::text IS NULL OR code = %(code)s)
            ORDER BY event_time ASC
        """
        params = {"instrument_id": instrument_id, "code": None if code is None else code.value}
        with psycopg.connect(self._conninfo) as conn, conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
        return [
            DataQualityEvent(
                event_id=r[0],
                dataset_type=r[1],
                instrument_id=r[2],
                severity=QualitySeverity(r[3]),
                code=QualityCode(r[4]),
                event_time=r[5],
                details=r[6],
                resolved_at=r[7],
            )
            for r in rows
        ]

    def resolve(self, event_id: uuid.UUID, resolved_at: datetime) -> bool:
        query = """
            UPDATE data_quality_events
            SET resolved_at = %s
            WHERE event_id = %s AND resolved_at IS NULL
        """
        with psycopg.connect(self._conninfo) as conn, conn.cursor() as cur:
            cur.execute(query, (resolved_at, event_id))
            conn.commit()
            return cur.rowcount == 1


class PostgresCandleSnapshotFactory:
    """CandleSnapshotFactory over one read-only REPEATABLE READ transaction:
    the snapshot is taken at the first query and every read through the
    yielded repository — verification and streaming cursors alike — sees that
    same point-in-time view until the context exits (T7 amendement 2)."""

    def __init__(self, conninfo: str) -> None:
        self._conninfo = conninfo

    @contextmanager
    def __call__(self) -> Iterator[PostgresCandleRepository]:
        with psycopg.connect(self._conninfo) as conn:
            conn.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ
            conn.read_only = True
            try:
                yield PostgresCandleRepository(connection=conn)
            finally:
                conn.rollback()


_DATASET_COLUMNS = """
    dataset_id, dataset_name, version, storage_uri, content_hash, source,
    start_time, end_time, status, metadata, created_at
"""


def _row_to_dataset(row: tuple[Any, ...]) -> Dataset:
    return Dataset(
        dataset_id=row[0],
        dataset_name=row[1],
        version=row[2],
        storage_uri=row[3],
        content_hash=row[4],
        source=row[5],
        start_time=row[6],
        end_time=row[7],
        status=row[8],
        metadata=row[9],
        created_at=row[10],
    )


class PostgresDatasetRepository:
    def __init__(self, conninfo: str) -> None:
        self._conninfo = conninfo

    def insert(self, dataset: Dataset) -> None:
        query = """
            INSERT INTO datasets (
                dataset_id, dataset_name, version, storage_uri, content_hash,
                source, start_time, end_time, status, metadata
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        with psycopg.connect(self._conninfo) as conn, conn.cursor() as cur:
            cur.execute(
                query,
                (
                    dataset.dataset_id,
                    dataset.dataset_name,
                    dataset.version,
                    dataset.storage_uri,
                    dataset.content_hash,
                    dataset.source,
                    dataset.start_time,
                    dataset.end_time,
                    dataset.status,
                    json.dumps(dataset.metadata) if dataset.metadata is not None else None,
                ),
            )
            conn.commit()

    def get(self, dataset_name: str, version: str) -> Dataset | None:
        query = f"SELECT {_DATASET_COLUMNS} FROM datasets WHERE dataset_name = %s AND version = %s"
        with psycopg.connect(self._conninfo) as conn, conn.cursor() as cur:
            cur.execute(query, (dataset_name, version))
            row = cur.fetchone()
        return None if row is None else _row_to_dataset(row)

    def list_all(self) -> list[Dataset]:
        query = f"SELECT {_DATASET_COLUMNS} FROM datasets ORDER BY created_at ASC"
        with psycopg.connect(self._conninfo) as conn, conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
        return [_row_to_dataset(r) for r in rows]


class PostgresAuditEventWriter:
    def __init__(self, conninfo: str) -> None:
        self._conninfo = conninfo

    def write(self, event: AuditEvent) -> None:
        query = """
            INSERT INTO audit_events (
                audit_event_id, actor_type, actor_id, action, resource_type,
                resource_id, environment, request_id, correlation_id, result, metadata
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        with psycopg.connect(self._conninfo) as conn, conn.cursor() as cur:
            cur.execute(
                query,
                (
                    event.audit_event_id,
                    event.actor_type.value,
                    event.actor_id,
                    event.action,
                    event.resource_type,
                    event.resource_id,
                    event.environment,
                    event.request_id,
                    event.correlation_id,
                    event.result.value,
                    json.dumps(event.metadata) if event.metadata is not None else None,
                ),
            )
            conn.commit()

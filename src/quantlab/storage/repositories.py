"""Repository interfaces (04-Storage-Engine §25-§26).

Business code depends on these Protocols, never on a storage vendor directly
(01-Vision §14). The PostgreSQL adapter implements them.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator, Sequence
from contextlib import AbstractContextManager
from datetime import datetime
from decimal import Decimal
from typing import Any, Protocol

from quantlab.audit.events import AuditEvent
from quantlab.domain.models import (
    Asset,
    Candle,
    DataQualityEvent,
    Dataset,
    Instrument,
    QualityCode,
    Timeframe,
    Venue,
)

# (open_time, open, high, low, close, volume, trade_count) — the market
# content of one candle, as stored. Used by the dataset hash stream.
CandleRow = tuple[datetime, Decimal, Decimal, Decimal, Decimal, Decimal, int | None]


class AssetRepository(Protocol):
    def get_by_symbol(self, symbol: str) -> Asset | None: ...
    def insert(self, asset: Asset) -> None: ...


class VenueRepository(Protocol):
    def get_by_code(self, code: str) -> Venue | None: ...
    def insert(self, venue: Venue) -> None: ...


class InstrumentRepository(Protocol):
    def get(self, instrument_id: uuid.UUID) -> Instrument | None: ...
    def get_by_venue_symbol(self, venue_id: uuid.UUID, venue_symbol: str) -> Instrument | None: ...
    def insert(self, instrument: Instrument) -> None: ...


class CandleRepository(Protocol):
    def insert_many(self, candles: Sequence[Candle]) -> int:
        """Bulk insert; duplicates (same instrument/timeframe/open_time/source)
        are skipped, never overwritten — historical data is immutable."""
        ...

    def read_range(
        self,
        instrument_id: uuid.UUID,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
    ) -> list[Candle]: ...

    def latest_open_time(
        self,
        instrument_id: uuid.UUID,
        timeframe: Timeframe,
        source: str,
    ) -> datetime | None:
        """Newest stored open_time for this series — the resume checkpoint of
        the historical download (derived from data, never from job state)."""
        ...

    def count_range(
        self,
        instrument_id: uuid.UUID,
        timeframe: Timeframe,
        source: str,
        start: datetime,
        end: datetime,
    ) -> int:
        """Number of stored candles with open_time in [start, end)."""
        ...

    def stream_candle_rows(
        self,
        instrument_id: uuid.UUID,
        timeframe: Timeframe,
        source: str,
        start: datetime,
        end: datetime,
        batch_size: int = 50_000,
    ) -> Iterator[Sequence[CandleRow]]:
        """Market content of [start, end) ordered by open_time, streamed in
        batches (server-side cursor): millions of rows are hashed without
        ever being materialized as domain models."""
        ...

    def stream_candles(
        self,
        instrument_id: uuid.UUID,
        timeframe: Timeframe,
        source: str,
        start: datetime,
        end: datetime,
        batch_size: int = 50_000,
    ) -> Iterator[Sequence[Candle]]:
        """Full domain candles of [start, end) ordered by open_time, streamed
        in batches — the replay read path."""
        ...

    def missing_ranges(
        self,
        instrument_id: uuid.UUID,
        timeframe: Timeframe,
        source: str,
        start: datetime,
        end: datetime,
    ) -> list[tuple[datetime, datetime]]:
        """Half-open [hole_start, hole_end) ranges of open_times missing from
        the stored series over [start, end), oldest first. Leading, interior
        and trailing holes are all reported; `start` and `end` must sit on the
        timeframe grid. An empty series yields the single hole [start, end)."""
        ...


class RawWsMessageWriter(Protocol):
    """Append-only journal of raw WebSocket messages (ADR-0001 A.2): no
    deduplication, everything the venue pushed is kept as pushed."""

    def insert(
        self,
        message_id: uuid.UUID,
        received_at: datetime,
        stream: str,
        payload: dict[str, Any],
    ) -> None: ...


class CandleSnapshotFactory(Protocol):
    """Opens a read-only, point-in-time view of the candle store. Everything
    executed against the yielded repository — integrity verification AND the
    streaming cursors of a replay — sees one single consistent snapshot,
    even while concurrent inserts land (PostgreSQL: one REPEATABLE READ
    transaction). The snapshot lives until the context exits."""

    def __call__(self) -> AbstractContextManager[CandleRepository]: ...


class DatasetRepository(Protocol):
    def insert(self, dataset: Dataset) -> None:
        """Publish a dataset. (dataset_name, version) is unique and the row
        is immutable once written (append-only trigger)."""
        ...

    def get(self, dataset_name: str, version: str) -> Dataset | None: ...

    def list_all(self) -> list[Dataset]:
        """All published datasets, oldest first."""
        ...


class AuditEventWriter(Protocol):
    def write(self, event: AuditEvent) -> None: ...


class DataQualityEventRepository(Protocol):
    def insert(self, event: DataQualityEvent) -> None: ...

    def list_unresolved(
        self,
        instrument_id: uuid.UUID | None = None,
        code: QualityCode | None = None,
    ) -> list[DataQualityEvent]:
        """Open anomalies (resolved_at IS NULL), oldest first; filters are ANDed."""
        ...

    def resolve(self, event_id: uuid.UUID, resolved_at: datetime) -> bool:
        """Mark one event resolved. Returns False if it was unknown or already
        resolved — the first resolution timestamp is never overwritten."""
        ...

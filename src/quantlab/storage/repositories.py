"""Repository interfaces (04-Storage-Engine §25-§26).

Business code depends on these Protocols, never on a storage vendor directly
(01-Vision §14). The PostgreSQL adapter implements them.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from quantlab.audit.events import AuditEvent
from quantlab.domain.models import (
    Asset,
    Candle,
    DataQualityEvent,
    Instrument,
    QualityCode,
    Timeframe,
    Venue,
)


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

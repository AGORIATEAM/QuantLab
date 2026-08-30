"""In-memory test doubles for repository protocols (mock the boundary,
not the internal logic — docs/17 §78)."""

from __future__ import annotations

import uuid
from datetime import datetime

from quantlab.audit.events import AuditEvent
from quantlab.domain.models import Candle, DataQualityEvent, Instrument, QualityCode, Timeframe


class InMemoryQualityEvents:
    """DataQualityEventRepository double."""

    def __init__(self) -> None:
        self.events: list[DataQualityEvent] = []

    def insert(self, event: DataQualityEvent) -> None:
        self.events.append(event)

    def list_unresolved(
        self,
        instrument_id: uuid.UUID | None = None,
        code: QualityCode | None = None,
    ) -> list[DataQualityEvent]:
        return sorted(
            (
                e
                for e in self.events
                if e.resolved_at is None
                and (instrument_id is None or e.instrument_id == instrument_id)
                and (code is None or e.code == code)
            ),
            key=lambda e: e.event_time,
        )

    def resolve(self, event_id: uuid.UUID, resolved_at: datetime) -> bool:
        for index, event in enumerate(self.events):
            if event.event_id == event_id and event.resolved_at is None:
                self.events[index] = event.model_copy(update={"resolved_at": resolved_at})
                return True
        return False


class InMemoryCandles:
    """CandleRepository double with the same uniqueness rule as the database."""

    def __init__(self) -> None:
        self.rows: dict[tuple[uuid.UUID, Timeframe, datetime, str], Candle] = {}

    def insert_many(self, candles: list[Candle]) -> int:
        inserted = 0
        for candle in candles:
            key = (candle.instrument_id, candle.timeframe, candle.open_time, candle.source)
            if key not in self.rows:
                self.rows[key] = candle
                inserted += 1
        return inserted

    def read_range(
        self,
        instrument_id: uuid.UUID,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
    ) -> list[Candle]:
        return sorted(
            (
                c
                for c in self.rows.values()
                if c.instrument_id == instrument_id
                and c.timeframe == timeframe
                and start <= c.open_time < end
            ),
            key=lambda c: c.open_time,
        )

    def latest_open_time(
        self,
        instrument_id: uuid.UUID,
        timeframe: Timeframe,
        source: str,
    ) -> datetime | None:
        times = [
            c.open_time
            for c in self.rows.values()
            if c.instrument_id == instrument_id and c.timeframe == timeframe and c.source == source
        ]
        return max(times) if times else None

    def missing_ranges(
        self,
        instrument_id: uuid.UUID,
        timeframe: Timeframe,
        source: str,
        start: datetime,
        end: datetime,
    ) -> list[tuple[datetime, datetime]]:
        times = sorted(
            c.open_time
            for c in self.rows.values()
            if c.instrument_id == instrument_id
            and c.timeframe == timeframe
            and c.source == source
            and start <= c.open_time < end
        )
        step = timeframe.duration
        holes: list[tuple[datetime, datetime]] = []
        cursor = start
        for open_time in times:
            if open_time > cursor:
                holes.append((cursor, open_time))
            cursor = open_time + step
        if cursor < end:
            holes.append((cursor, end))
        return holes


class GridSource:
    """HistoricalCandleSource double serving a fixed candle list."""

    def __init__(self, candles: list[Candle]) -> None:
        self.candles = sorted(candles, key=lambda c: c.open_time)
        self.calls: list[tuple[datetime, datetime, int]] = []

    def fetch_candles(
        self,
        instrument: Instrument,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
        limit: int = 1000,
    ) -> list[Candle]:
        self.calls.append((start, end, limit))
        return [c for c in self.candles if start <= c.open_time < end][:limit]

    def health_check(self) -> bool:
        return True


class RecordingAudit:
    """AuditEventWriter double."""

    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def write(self, event: AuditEvent) -> None:
        self.events.append(event)

"""In-memory test doubles for repository protocols (mock the boundary,
not the internal logic — docs/17 §78)."""

from __future__ import annotations

import uuid
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import datetime

from quantlab.audit.events import AuditEvent
from quantlab.domain.models import (
    Candle,
    DataQualityEvent,
    Dataset,
    Instrument,
    QualityCode,
    Timeframe,
)
from quantlab.storage.repositories import CandleRow


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

    def _rows_in_range(
        self,
        instrument_id: uuid.UUID,
        timeframe: Timeframe,
        source: str,
        start: datetime,
        end: datetime,
    ) -> list[Candle]:
        return sorted(
            (
                c
                for c in self.rows.values()
                if c.instrument_id == instrument_id
                and c.timeframe == timeframe
                and c.source == source
                and start <= c.open_time < end
            ),
            key=lambda c: c.open_time,
        )

    def count_range(
        self,
        instrument_id: uuid.UUID,
        timeframe: Timeframe,
        source: str,
        start: datetime,
        end: datetime,
    ) -> int:
        return len(self._rows_in_range(instrument_id, timeframe, source, start, end))

    def stream_candle_rows(
        self,
        instrument_id: uuid.UUID,
        timeframe: Timeframe,
        source: str,
        start: datetime,
        end: datetime,
        batch_size: int = 50_000,
    ) -> Iterator[Sequence[CandleRow]]:
        rows = [
            (c.open_time, c.open, c.high, c.low, c.close, c.volume, c.trade_count)
            for c in self._rows_in_range(instrument_id, timeframe, source, start, end)
        ]
        for i in range(0, len(rows), batch_size):
            yield rows[i : i + batch_size]

    def stream_candles(
        self,
        instrument_id: uuid.UUID,
        timeframe: Timeframe,
        source: str,
        start: datetime,
        end: datetime,
        batch_size: int = 50_000,
    ) -> Iterator[Sequence[Candle]]:
        rows = self._rows_in_range(instrument_id, timeframe, source, start, end)
        for i in range(0, len(rows), batch_size):
            yield rows[i : i + batch_size]

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


class InMemoryRawWsMessages:
    """RawWsMessageWriter double — a plain journal, duplicates kept."""

    def __init__(self) -> None:
        self.rows: list[tuple[uuid.UUID, datetime, str, dict[str, object]]] = []

    def insert(
        self,
        message_id: uuid.UUID,
        received_at: datetime,
        stream: str,
        payload: dict[str, object],
    ) -> None:
        self.rows.append((message_id, received_at, stream, payload))

    def latency_stats(self, since: datetime) -> tuple[float, float, float, int] | None:
        lats = []
        for _id, received_at, _stream, payload in self.rows:
            if received_at < since:
                continue
            data = payload.get("data")
            if isinstance(data, dict) and isinstance(data.get("E"), int):
                lats.append(received_at.timestamp() * 1000 - data["E"])
        if not lats:
            return None
        lats.sort()
        p95 = lats[min(len(lats) - 1, round(0.95 * (len(lats) - 1)))]
        return (sum(lats) / len(lats), p95, lats[-1], len(lats))


class InMemorySnapshotFactory:
    """CandleSnapshotFactory double: the yielded repository is a copy taken
    at entry — inserts into the live repository during iteration are
    invisible, mirroring the REPEATABLE READ snapshot."""

    def __init__(self, live: InMemoryCandles) -> None:
        self._live = live

    @contextmanager
    def __call__(self) -> Iterator[InMemoryCandles]:
        frozen = InMemoryCandles()
        frozen.rows = dict(self._live.rows)
        yield frozen


class InMemoryDatasets:
    """DatasetRepository double with the same uniqueness rule as the table."""

    def __init__(self) -> None:
        self.rows: dict[tuple[str, str], Dataset] = {}

    def insert(self, dataset: Dataset) -> None:
        key = (dataset.dataset_name, dataset.version)
        if key in self.rows:
            raise ValueError(f"duplicate dataset {key}")
        self.rows[key] = dataset

    def get(self, dataset_name: str, version: str) -> Dataset | None:
        return self.rows.get((dataset_name, version))

    def list_all(self) -> list[Dataset]:
        return list(self.rows.values())


class RecordingAudit:
    """AuditEventWriter double."""

    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def write(self, event: AuditEvent) -> None:
        self.events.append(event)

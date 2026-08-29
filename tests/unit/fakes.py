"""In-memory test doubles for repository protocols (mock the boundary,
not the internal logic — docs/17 §78)."""

from __future__ import annotations

import uuid
from datetime import datetime

from quantlab.domain.models import DataQualityEvent, QualityCode


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

"""PostgresDataQualityEventRepository against a real database (T1)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from quantlab.core.ids import new_id
from quantlab.domain.models import DataQualityEvent, QualityCode, QualitySeverity
from quantlab.storage.postgres.adapter import PostgresDataQualityEventRepository

pytestmark = pytest.mark.integration

EVENT_TIME = datetime(2026, 8, 26, 10, 0, tzinfo=UTC)


def make_event(instrument_id: uuid.UUID | None, **overrides: object) -> DataQualityEvent:
    base: dict[str, object] = {
        "event_id": new_id(),
        "dataset_type": "candles",
        "instrument_id": instrument_id,
        "severity": QualitySeverity.WARNING,
        "code": QualityCode.GAP,
        "event_time": EVENT_TIME,
        "details": {"missing_count": 3},
    }
    base.update(overrides)
    return DataQualityEvent(**base)  # type: ignore[arg-type]


def test_insert_and_list_unresolved_roundtrip(
    database_url: str, btc_instrument_id: uuid.UUID
) -> None:
    repo = PostgresDataQualityEventRepository(database_url)
    gap = make_event(btc_instrument_id)
    dataset_level = make_event(None, code=QualityCode.STALE_DATA, details=None)
    repo.insert(gap)
    repo.insert(dataset_level)

    unresolved = repo.list_unresolved(instrument_id=btc_instrument_id, code=QualityCode.GAP)
    assert gap in unresolved
    assert dataset_level not in unresolved

    fetched = next(e for e in unresolved if e.event_id == gap.event_id)
    assert fetched == gap  # JSONB details, enums and UTC timestamps round-trip exactly


def test_resolve_is_one_shot(database_url: str, btc_instrument_id: uuid.UUID) -> None:
    repo = PostgresDataQualityEventRepository(database_url)
    event = make_event(btc_instrument_id, code=QualityCode.DUPLICATE_SKIPPED)
    repo.insert(event)
    resolved_at = datetime(2026, 8, 26, 11, 0, tzinfo=UTC)

    assert repo.resolve(event.event_id, resolved_at) is True
    assert repo.resolve(event.event_id, resolved_at) is False  # already resolved
    assert repo.resolve(new_id(), resolved_at) is False  # unknown event

    ids = [e.event_id for e in repo.list_unresolved(instrument_id=btc_instrument_id)]
    assert event.event_id not in ids


def test_unknown_instrument_is_rejected_by_foreign_key(database_url: str) -> None:
    import psycopg

    repo = PostgresDataQualityEventRepository(database_url)
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        repo.insert(make_event(new_id()))


def test_list_unresolved_orders_oldest_first(
    database_url: str, btc_instrument_id: uuid.UUID
) -> None:
    repo = PostgresDataQualityEventRepository(database_url)
    late = make_event(
        btc_instrument_id,
        code=QualityCode.OUT_OF_ORDER,
        event_time=datetime(2026, 8, 26, 12, 0, tzinfo=UTC),
    )
    early = make_event(
        btc_instrument_id,
        code=QualityCode.OUT_OF_ORDER,
        event_time=datetime(2026, 8, 26, 9, 0, tzinfo=UTC),
    )
    repo.insert(late)
    repo.insert(early)
    events = repo.list_unresolved(instrument_id=btc_instrument_id, code=QualityCode.OUT_OF_ORDER)
    assert [e.event_id for e in events] == [early.event_id, late.event_id]

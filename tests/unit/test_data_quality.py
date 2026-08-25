"""DataQualityEvent invariants: UTC-aware timestamps, typed severity/code."""

import uuid
from datetime import UTC, datetime, timedelta, timezone

import pytest

from quantlab.domain.models import DataQualityEvent, QualityCode, QualitySeverity

EVENT_TIME = datetime(2026, 8, 26, 12, 0, tzinfo=UTC)


def make_event(**overrides: object) -> DataQualityEvent:
    base: dict[str, object] = {
        "event_id": uuid.uuid4(),
        "dataset_type": "candles",
        "instrument_id": uuid.uuid4(),
        "severity": QualitySeverity.WARNING,
        "code": QualityCode.GAP,
        "event_time": EVENT_TIME,
        "details": {"missing_from": "2026-08-26T10:15:00Z", "missing_count": 3},
    }
    base.update(overrides)
    return DataQualityEvent(**base)  # type: ignore[arg-type]


def test_valid_event() -> None:
    event = make_event()
    assert event.code is QualityCode.GAP
    assert event.resolved_at is None


def test_instrument_id_may_be_null_for_dataset_level_events() -> None:
    assert make_event(instrument_id=None).instrument_id is None


def test_naive_event_time_rejected() -> None:
    with pytest.raises(ValueError):
        make_event(event_time=datetime(2026, 8, 26, 12, 0))


def test_naive_resolved_at_rejected() -> None:
    with pytest.raises(ValueError):
        make_event(resolved_at=datetime(2026, 8, 26, 13, 0))


def test_aware_non_utc_times_are_normalized_to_utc() -> None:
    paris = timezone(timedelta(hours=2))
    event = make_event(event_time=datetime(2026, 8, 26, 14, 0, tzinfo=paris))
    assert event.event_time == EVENT_TIME
    assert event.event_time.tzinfo == UTC


def test_unknown_code_rejected() -> None:
    with pytest.raises(ValueError):
        make_event(code="SOMETHING_ELSE")

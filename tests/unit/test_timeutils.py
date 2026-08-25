from datetime import UTC, datetime, timedelta, timezone

import pytest

from quantlab.core.timeutils import require_utc, utc_now


def test_utc_now_is_aware_utc() -> None:
    now = utc_now()
    assert now.tzinfo is UTC


def test_require_utc_rejects_naive() -> None:
    with pytest.raises(ValueError):
        require_utc(datetime(2026, 1, 1))


def test_require_utc_normalizes_offsets() -> None:
    paris = timezone(timedelta(hours=2))
    value = datetime(2026, 8, 25, 12, 0, tzinfo=paris)
    assert require_utc(value).hour == 10

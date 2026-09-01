"""Clock abstraction: wall clock delegation, simulated monotonicity."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from quantlab.core.clock import SimulatedClock, WallClock
from quantlab.core.timeutils import utc_now

T0 = datetime(2026, 8, 1, tzinfo=UTC)


def test_wall_clock_tracks_real_time() -> None:
    now = WallClock().now()
    assert abs((now - utc_now()).total_seconds()) < 1


def test_simulated_clock_advances_and_holds() -> None:
    clock = SimulatedClock(T0)
    assert clock.now() == T0
    clock.advance_to(T0 + timedelta(hours=1))
    assert clock.now() == T0 + timedelta(hours=1)
    clock.advance_to(clock.now())  # advancing to the same instant is a no-op
    assert clock.now() == T0 + timedelta(hours=1)


def test_simulated_clock_refuses_to_move_backward() -> None:
    clock = SimulatedClock(T0)
    clock.advance_to(T0 + timedelta(hours=2))
    with pytest.raises(ValueError, match="cannot move backward"):
        clock.advance_to(T0 + timedelta(hours=1))


def test_simulated_clock_rejects_naive_datetimes() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        SimulatedClock(datetime(2026, 8, 1))

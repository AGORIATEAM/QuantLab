"""Time source abstraction (T7, docs/03 §40, roadmap §31).

Downstream engines (analysis, scoring, decision — Phase 2) must never call
utc_now() directly: they receive a Clock. In research the replay engine owns
a SimulatedClock and is the only writer of time; in live the same code runs
against WallClock. Any utc_now() call inside an engine is a look-ahead bug
waiting to happen.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from quantlab.core.timeutils import require_utc, utc_now


class Clock(Protocol):
    def now(self) -> datetime: ...


class WallClock:
    """Real time — the live path."""

    def now(self) -> datetime:
        return utc_now()


class SimulatedClock:
    """Replay-driven time. Strictly monotonic: moving backward is refused,
    because a consumer that observed t must never see the world at t' < t."""

    def __init__(self, start: datetime) -> None:
        self._now = require_utc(start, "start")

    def now(self) -> datetime:
        return self._now

    def advance_to(self, ts: datetime) -> None:
        ts = require_utc(ts, "ts")
        if ts < self._now:
            raise ValueError(
                f"simulated clock cannot move backward ({self._now.isoformat()} "
                f"-> {ts.isoformat()})"
            )
        self._now = ts

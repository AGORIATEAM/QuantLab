"""ADR-0003 equivalence tooling.

LoggingSimulator subclasses the untouched Decimal reference to journal
trades (entry/exit candle open_time, side, prices, R) — the reference's
behavior is not modified, only observed. Comparators implement the ADR
tolerances: integer counters and timestamps exact, monetary/R values at
relative 1e-9.
"""

from __future__ import annotations

from decimal import Decimal

from quantlab.data.replay import ReplayEvent
from quantlab.research.h1 import H1Simulator
from quantlab.structure.engine import StructureEvent

REL_TOLERANCE = 1e-9

SlowTrade = tuple[int, int, int, float, float, float]  # entry_ots, exit_ots, side, entry, exit, r


class LoggingSimulator(H1Simulator):
    """Reference simulator + trade journal, without touching the reference."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self.trade_log: list[SlowTrade] = []
        self._current_ots = 0
        self._entry_snapshot: tuple[int, Decimal] | None = None

    def on_5m(self, event: ReplayEvent, structure_events: list[StructureEvent]) -> None:
        self._current_ots = int(event.candle.open_time.timestamp())
        super().on_5m(event, structure_events)

    def _open_position(self, side: int, raw_price: Decimal, stop: Decimal) -> None:
        super()._open_position(side, raw_price, stop)
        if self._position is not None:
            self._entry_snapshot = (self._current_ots, self._position.entry)

    def _close_position(self, raw_price: Decimal) -> None:
        position = self._position
        assert position is not None
        r_before = self.metrics.sum_r
        price = (
            raw_price * (1 - self._fill.half_spread)
            if position.side > 0
            else raw_price * (1 + self._fill.half_spread)
        )
        super()._close_position(raw_price)
        assert self._entry_snapshot is not None
        entry_ots, entry_price = self._entry_snapshot
        self.trade_log.append(
            (
                entry_ots,
                self._current_ots,
                position.side,
                float(entry_price),
                float(price),
                float(self.metrics.sum_r - r_before),
            )
        )


def rel_equal(a: float, b: float, rel: float = REL_TOLERANCE) -> bool:
    scale = max(abs(a), abs(b), 1.0)
    return abs(a - b) <= rel * scale


def compare_trade_logs(
    slow: list[SlowTrade],
    fast: list[tuple[int, int, int, float, float, float]],
    label: str,
) -> list[str]:
    """Trade-by-trade comparison (ADR-0003 level 2). Returns differences."""
    diffs: list[str] = []
    if len(slow) != len(fast):
        return [f"{label}: trade count {len(slow)} (slow) != {len(fast)} (fast)"]
    for i, (s, f) in enumerate(zip(slow, fast, strict=True)):
        if s[0] != f[0] or s[1] != f[1] or s[2] != f[2]:
            diffs.append(f"{label} trade {i}: timing/side {s[:3]} != {f[:3]}")
            continue
        for name, sv, fv in (("entry", s[3], f[3]), ("exit", s[4], f[4]), ("r", s[5], f[5])):
            if not rel_equal(sv, fv):
                diffs.append(f"{label} trade {i}: {name} {sv!r} != {fv!r}")
    return diffs


INT_FIELDS = {"trades", "skipped_min_stop", "ignored_in_position", "n_5m", "n_1h"}
KEY_FIELDS = ["n_5m", "n_1h", "atr_mult", "buffer", "r_target", "min_stop_atr"]


def compare_metric_rows(
    reference: list[dict[str, str]],
    candidate: list[dict[str, object]],
    label: str,
) -> list[str]:
    """Aggregate comparison (ADR-0003 level 1) against a reference CSV."""
    diffs: list[str] = []
    if len(reference) != len(candidate):
        return [f"{label}: {len(reference)} reference rows != {len(candidate)} candidate rows"]
    by_key = {tuple(str(r[k]) for k in KEY_FIELDS): r for r in candidate}
    for ref in reference:
        key = tuple(_canon_param(ref[k]) for k in KEY_FIELDS)
        cand = by_key.get(key)
        if cand is None:
            diffs.append(f"{label}: configuration {key} missing from candidate")
            continue
        for field, ref_value in ref.items():
            if field in KEY_FIELDS:
                continue
            cand_value = str(cand[field])
            if field in INT_FIELDS:
                if int(ref_value) != int(cand_value):
                    diffs.append(f"{label} {key} {field}: {ref_value} != {cand_value} (exact)")
            elif ref_value == "" or cand_value == "":
                if ref_value != cand_value:
                    diffs.append(f"{label} {key} {field}: {ref_value!r} != {cand_value!r}")
            elif not rel_equal(float(ref_value), float(cand_value)):
                diffs.append(f"{label} {key} {field}: {ref_value} != {cand_value}")
    return diffs


def _canon_param(value: str) -> str:
    # golden CSV writes Decimal params ("1.5", "0", "0.1"); the fast CSV
    # writes the same canonical strings — normalize trailing zeros anyway
    if value in ("", None):
        return ""
    d = Decimal(value)
    return str(d.normalize()) if d == d.to_integral() else str(d)

"""EXP-20260902-003 (H4) Decimal reference simulator.

Labeling design (frozen 2026-09-02): the H3 trade population is UNCHANGED
— same signals, fills, stops, exits, sizing. Each trade is labeled at the
signal close by the localization of the SWEPT LEVEL (BreakEvent.level)
against the previous UTC day's volume profile, via the frozen classifier
(quantlab.profile.classify_level, config e1e53c71). Per-(side, bucket)
accumulators feed the per-bucket report; the refutation criteria read the
PRIMARY subset: long trades labeled sous_val UNION short trades labeled
sur_vah.

Frozen addition: primary_ignored counts sweep signals swallowed by an
open position (any label) that WOULD have been primary — the input to the
primary swallowing share of the IS report (conditions a potential Hyp-5).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC
from decimal import Decimal

from quantlab.domain.models import Candle
from quantlab.profile import BUCKETS, VolumeProfileEngine, classify_level
from quantlab.research.fast.equivalence import LoggingSimulator
from quantlab.research.h3 import H3Simulator
from quantlab.structure.breaks import BreakDirection, BreakKind
from quantlab.structure.engine import StructureEvent, StructureEventType
from quantlab.structure.state import StructureState

ZERO = Decimal(0)
LABEL_INDEX = {name: i for i, name in enumerate(BUCKETS)}
SOUS_VAL = LABEL_INDEX["sous_val"]
SUR_VAH = LABEL_INDEX["sur_vah"]


def is_primary(side: int, bucket: int) -> bool:
    """Primary subset: long x sous_val UNION short x sur_vah (frozen)."""
    return (side > 0 and bucket == SOUS_VAL) or (side < 0 and bucket == SUR_VAH)


@dataclass
class BucketStats:
    trades: int = 0
    wins: int = 0
    sum_r: Decimal = field(default_factory=lambda: ZERO)
    pos_r: Decimal = field(default_factory=lambda: ZERO)  # sum of positive R
    neg_r: Decimal = field(default_factory=lambda: ZERO)  # |sum of non-positive R|
    sum_cost_r: Decimal = field(default_factory=lambda: ZERO)
    sum_stop_pct: Decimal = field(default_factory=lambda: ZERO)
    dominated: int = 0


class H4Simulator(H3Simulator):
    """H3 trading, H4 labeling. `_engine_1h`/`_key_1h` hold the slow
    context, `_profiles` the shared (config-independent) profile engine
    fed by the harness BEFORE this simulator sees the candle."""

    def __init__(self, *args: object, profiles: VolumeProfileEngine, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self._profiles = profiles
        self.bucket_stats = {
            (side, bucket): BucketStats() for side in (1, -1) for bucket in range(len(BUCKETS))
        }
        self.primary_ignored = 0
        self.label_log: list[tuple[int, int]] = []  # (side, bucket) per closed trade
        self._pending_label = 0
        self._open_label = 0
        self._open_dominated = False

    @staticmethod
    def _context_side(context_state: StructureState, direction: BreakDirection) -> int:
        if context_state is StructureState.BULLISH and direction is BreakDirection.BEARISH:
            return 1  # low swept while bullish -> long
        if context_state is StructureState.BEARISH and direction is BreakDirection.BULLISH:
            return -1  # high swept while bearish -> short
        return 0

    def _open_position(self, side: int, raw_price: Decimal, stop: Decimal) -> None:
        had_position = self._position is not None
        super()._open_position(side, raw_price, stop)
        if self._position is not None and not had_position:
            self._open_label = self._pending_label
            self._open_dominated = self._pending_atr_dominated

    def _close_position(self, raw_price: Decimal) -> None:
        position = self._position
        assert position is not None
        m = self.metrics
        before = (m.sum_r, m.sum_cost_r, m.sum_stop_pct, m.wins)
        super()._close_position(raw_price)
        stats = self.bucket_stats[(1 if position.side > 0 else -1, self._open_label)]
        stats.trades += 1
        stats.wins += m.wins - before[3]
        r_delta = m.sum_r - before[0]
        stats.sum_r += r_delta
        if r_delta > 0:
            stats.pos_r += r_delta
        else:
            stats.neg_r += -r_delta
        stats.sum_cost_r += m.sum_cost_r - before[1]
        stats.sum_stop_pct += m.sum_stop_pct - before[2]
        if self._open_dominated:
            stats.dominated += 1
        self.label_log.append((position.side, self._open_label))

    def _signals(self, structure_events: list[StructureEvent], candle: Candle) -> None:
        context_state = self._engine_1h.state_of(self._key_1h)
        signal_day = candle.open_time.astimezone(UTC).date()
        profile = self._profiles.previous(self._key_5m)
        for out in structure_events:
            if out.event_type is not StructureEventType.STRUCTURE_BREAK or out.brk is None:
                continue
            brk = out.brk
            if brk.kind is BreakKind.CHOCH and self._position is not None:
                against = (
                    brk.direction is BreakDirection.BEARISH
                    if self._position.side > 0
                    else brk.direction is BreakDirection.BULLISH
                )
                if against:
                    self._exit_pending = True
            if brk.kind is not BreakKind.WICK_BREAK:
                continue
            if self._position is not None or self._entry_pending is not None:
                self.metrics.ignored_in_position += 1
                # frozen addition: would this swallowed sweep have been primary?
                side = self._context_side(context_state, brk.direction)
                if side != 0:
                    atr = self._engine_5m.runtime(self._key_5m).detector.atr.value
                    if atr is not None:
                        label = LABEL_INDEX[classify_level(brk.level, atr, profile, signal_day)]
                        if is_primary(side, label):
                            self.primary_ignored += 1
                continue
            side = self._context_side(context_state, brk.direction)
            if side == 0:
                continue
            wick_distance = (candle.close - brk.break_price) * side
            if wick_distance <= 0:
                continue
            atr = self._engine_5m.runtime(self._key_5m).detector.atr.value
            if atr is None:
                continue  # unreachable post-ready, kept for symmetry
            noise_floor = self.k_stop * atr
            distance = max(wick_distance, noise_floor)
            stop = candle.close - side * distance
            self._pending_label = LABEL_INDEX[classify_level(brk.level, atr, profile, signal_day)]
            self._pending_atr_dominated = noise_floor > wick_distance
            self._entry_pending = (side, stop)


class H4LoggingSimulator(LoggingSimulator, H4Simulator):
    """H4 reference with the trade journal (MRO: logging wraps H4)."""

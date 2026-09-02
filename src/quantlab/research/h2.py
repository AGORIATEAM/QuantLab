"""EXP-20260902-001 (H2) Decimal reference simulator.

Everything except the entry signal is inherited verbatim from the
equivalence-hardened H1 reference (fills, pessimistic ambiguities, sizing,
cap, exits, metrics). The override:

- signal = WICK_BREAK of a confirmed 5m swing AGAINST the slow context
  (context BULLISH + LOW-side sweep -> long; context BEARISH + HIGH-side
  sweep -> short; NEUTRAL/UNKNOWN -> nothing) — the recovery close is
  intrinsic to WICK_BREAK;
- stop = the sweep wick extreme (BreakEvent.break_price), the natural
  invalidation point;
- min_stop_atr measured against ATR_5m at the signal close, trade SKIPPED
  (never widened);
- a sweep signal while in position (or already pending) is ignored, no
  pyramiding — counted like H1's ignored signals.

The 5m CHoCH exit is inherited unchanged (H1Simulator._signals handled
both entry and CHoCH; this override re-implements the loop with the H2
entry trigger and the same CHoCH handling).
"""

from __future__ import annotations

from quantlab.domain.models import Candle
from quantlab.research.fast.equivalence import LoggingSimulator
from quantlab.research.h1 import H1Simulator
from quantlab.structure.breaks import BreakDirection, BreakKind
from quantlab.structure.engine import StructureEvent, StructureEventType
from quantlab.structure.state import StructureState


class H2Simulator(H1Simulator):
    """H1 machinery, H2 entry trigger. `_engine_1h` holds the SLOW CONTEXT
    engine (1h or 4h) and `_key_1h` its series key."""

    def _signals(self, structure_events: list[StructureEvent], candle: Candle) -> None:
        context_state = self._engine_1h.state_of(self._key_1h)
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
                continue
            # sweep against the slow context, recovery close intrinsic
            if context_state is StructureState.BULLISH and brk.direction is BreakDirection.BEARISH:
                side = 1  # low swept while bullish -> long
            elif (
                context_state is StructureState.BEARISH and brk.direction is BreakDirection.BULLISH
            ):
                side = -1  # high swept while bearish -> short
            else:
                continue
            stop = brk.break_price  # the wick extreme
            distance = (candle.close - stop) * side
            if distance <= 0:
                continue
            atr = self._engine_5m.runtime(self._key_5m).detector.atr.value
            if atr is not None and distance < self.config.min_stop_atr * atr:
                self.metrics.skipped_min_stop += 1
                continue
            self._entry_pending = (side, stop)


class H2LoggingSimulator(LoggingSimulator, H2Simulator):
    """H2 reference with the trade journal (MRO: logging wraps H2 signals)."""

"""EXP-20260902-002 (H3) Decimal reference simulator.

H2 machinery (sweep signal, CHoCH exit, fills, sizing, metrics) with the
frozen stop change: the stop DISTANCE is max(wick extreme distance,
k x ATR_15m at the signal close), anchored on the opposite side of the
position — a statistical invalidation (noise) anchored below the
structural one (the wick). No min_stop filter: the k x ATR floor makes it
redundant by construction. Trades whose distance came from the ATR term
(k x ATR > wick distance) are counted in metrics.stop_atr_dominated.
"""

from __future__ import annotations

from decimal import Decimal

from quantlab.domain.models import Candle
from quantlab.research.fast.equivalence import LoggingSimulator
from quantlab.research.h2 import H2Simulator
from quantlab.structure.breaks import BreakDirection, BreakKind
from quantlab.structure.engine import StructureEvent, StructureEventType
from quantlab.structure.state import StructureState


class H3Simulator(H2Simulator):
    def __init__(self, *args: object, k_stop: Decimal, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self.k_stop = k_stop
        self._pending_atr_dominated = False

    def _open_position(self, side: int, raw_price: Decimal, stop: Decimal) -> None:
        had_position = self._position is not None
        super()._open_position(side, raw_price, stop)
        if self._position is not None and not had_position and self._pending_atr_dominated:
            self.metrics.stop_atr_dominated += 1

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
            if context_state is StructureState.BULLISH and brk.direction is BreakDirection.BEARISH:
                side = 1
            elif (
                context_state is StructureState.BEARISH and brk.direction is BreakDirection.BULLISH
            ):
                side = -1
            else:
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
            self._pending_atr_dominated = noise_floor > wick_distance
            self._entry_pending = (side, stop)


class H3LoggingSimulator(LoggingSimulator, H3Simulator):
    """H3 reference with the trade journal (MRO: logging wraps H3 signals)."""

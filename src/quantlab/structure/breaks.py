"""BOS / CHoCH / WICK_BREAK detection (docs/06 §18-§23, règles 3-4).

Precise semantics (§41):

- **Reference level** = the last CONFIRMED swing of the relevant kind, as
  kept by the alternating sequence. A level arms when that swing is
  appended or replaced (a replacement IS a new confirmed swing of the
  kind: the level moved, it re-arms).
- **One level breaks once** (règle 4): a validated BOS/CHoCH CONSUMES its
  reference swing; the next break of that side requires a NEW confirmed
  swing. N closes beyond the same level yield exactly one event.
- **Validation** (§19): method A — close beyond the level; method B —
  close beyond level ± ATR x breakout_buffer. Method B without a warm ATR
  validates nothing (the engine is not ready before the ATR is, règle 5).
- **WICK_BREAK** (§20): wick beyond the level with a close that fails
  validation. Recorded separately, NEVER a BOS, and it does NOT consume
  the level (règle 4 applies to BOS/CHoCH only) — emitted at most once per
  armed swing per side to keep the journal readable.
- **Kind** (§18, §22-§23): a validated break in the direction of the
  dominant structure is a BOS; against it, a CHOCH. With no dominant
  structure (NEUTRAL/UNKNOWN) a validated break is labelled BOS with its
  direction — a CHoCH requires an opposite dominant structure to exist.
  Breaks are events only: the state machine never reads them (règle 3).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from quantlab.domain.models import Candle
from quantlab.structure.state import StructureState
from quantlab.structure.swings import SwingEvent, SwingKind


class BreakKind(StrEnum):
    BOS = "BOS"
    CHOCH = "CHOCH"
    WICK_BREAK = "WICK_BREAK"


class BreakDirection(StrEnum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"


class ValidationMethod(StrEnum):
    CLOSE = "close"  # §19 method A
    ATR_BUFFER = "atr_buffer"  # §19 method B


@dataclass(frozen=True)
class BreakEvent:
    kind: BreakKind
    direction: BreakDirection
    level: Decimal
    break_price: Decimal  # close (BOS/CHOCH) or the wick extreme (WICK_BREAK)
    reference_pivot: datetime  # pivot_timestamp of the consumed/broken swing
    event_timestamp: datetime  # close_time of the breaking candle
    available_at: datetime  # same candle close: known when the candle closes


@dataclass
class _ArmedLevel:
    swing: SwingEvent
    wick_flagged: bool = False


class BreakDetector:
    """Tracks the two armed levels (last high / last low) and evaluates
    each candle at its close."""

    def __init__(self, validation: ValidationMethod, breakout_buffer: Decimal = Decimal(0)) -> None:
        self.validation = validation
        self.breakout_buffer = breakout_buffer
        self._armed: dict[SwingKind, _ArmedLevel | None] = {
            SwingKind.HIGH: None,
            SwingKind.LOW: None,
        }

    def arm(self, swing: SwingEvent) -> None:
        """Called on every sequence APPENDED/REPLACED swing: the level of
        that side re-arms (a replacement is a new confirmed swing)."""
        self._armed[swing.kind] = _ArmedLevel(swing)

    def update(
        self, candle: Candle, state: StructureState, atr: Decimal | None
    ) -> list[BreakEvent]:
        events: list[BreakEvent] = []
        up = self._evaluate(candle, state, atr, SwingKind.HIGH)
        if up is not None:
            events.append(up)
        down = self._evaluate(candle, state, atr, SwingKind.LOW)
        if down is not None:
            events.append(down)
        return events

    def _threshold(self, level: Decimal, kind: SwingKind, atr: Decimal | None) -> Decimal | None:
        if self.validation is ValidationMethod.CLOSE:
            return level
        if atr is None:
            return None  # method B cannot validate without a warm ATR
        buffer = atr * self.breakout_buffer
        return level + buffer if kind is SwingKind.HIGH else level - buffer

    def _evaluate(
        self, candle: Candle, state: StructureState, atr: Decimal | None, kind: SwingKind
    ) -> BreakEvent | None:
        armed = self._armed[kind]
        if armed is None:
            return None
        level = armed.swing.price
        threshold = self._threshold(level, kind, atr)
        if kind is SwingKind.HIGH:
            validated = threshold is not None and candle.close > threshold
            wicked = candle.high > level and not validated
            direction = BreakDirection.BULLISH
            wick_price = candle.high
            with_structure = state is StructureState.BULLISH
            against_structure = state is StructureState.BEARISH
        else:
            validated = threshold is not None and candle.close < threshold
            wicked = candle.low < level and not validated
            direction = BreakDirection.BEARISH
            wick_price = candle.low
            with_structure = state is StructureState.BEARISH
            against_structure = state is StructureState.BULLISH

        if validated:
            self._armed[kind] = None  # consumed: one level breaks once (règle 4)
            kind_out = BreakKind.BOS if with_structure or not against_structure else BreakKind.CHOCH
            return BreakEvent(
                kind=kind_out,
                direction=direction,
                level=level,
                break_price=candle.close,
                reference_pivot=armed.swing.pivot_timestamp,
                event_timestamp=candle.close_time,
                available_at=candle.close_time,
            )
        if wicked and not armed.wick_flagged:
            armed.wick_flagged = True  # once per armed swing; level stays armed
            return BreakEvent(
                kind=BreakKind.WICK_BREAK,
                direction=direction,
                level=level,
                break_price=wick_price,
                reference_pivot=armed.swing.pivot_timestamp,
                event_timestamp=candle.close_time,
                available_at=candle.close_time,
            )
        return None

"""Swing detection with deferred confirmation (docs/06 §8-§11, §41 precise).

Definitions — no ambiguity (§41):

- **Fractal swing high** at the center of a (2n+1)-candle window:
  ``high[i] > every high of the n candles BEFORE`` and
  ``high[i] >= every high of the n candles AFTER`` (§8; symmetric for lows,
  strict before / <= after). A swing that pivots at candle t therefore
  EXISTS only at the close of candle t+n: SwingEvent carries
  ``pivot_timestamp`` (pivot candle open_time) and
  ``confirmation_timestamp`` (confirming candle close_time — the
  available_at of §56). A detector physically cannot emit earlier: it only
  ever sees candles already received (§10, §55).

- **Alternation (zigzag)**: the confirmed sequence always alternates
  HIGH/LOW. Two consecutive swings of the same kind keep only the extreme
  (higher high / lower low); the other is discarded. A same-kind
  replacement extends the current leg. (Règle 1 de la revue.)

- **ATR variant** (§11): a candidate that would START A NEW LEG (opposite
  kind to the last kept swing) must span at least ``ATR x multiplier``
  measured FROM THE LAST CONFIRMED OPPOSITE SWING at confirmation time;
  otherwise the candidate is rejected and DISAPPEARS entirely — it can
  never come back (règle 2). Same-kind candidates are handled by
  alternation alone (extending a leg never shrinks its amplitude). Until
  the ATR is warm, candidates are rejected (the engine is not ready
  anyway, règle 5).

Both detectors expose the same interface: ``update(candle) ->
list[SwingEvent]`` (raw confirmed candidates), ``min_leg()`` (None for the
pure fractal) and ``ready``.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from quantlab.domain.models import Candle
from quantlab.structure.atr import WilderAtr


class SwingKind(StrEnum):
    HIGH = "HIGH"
    LOW = "LOW"


@dataclass(frozen=True)
class SwingEvent:
    kind: SwingKind
    price: Decimal
    pivot_timestamp: datetime  # open_time of the pivot candle
    confirmation_timestamp: datetime  # close_time of the confirming candle


class FractalSwingDetector:
    """Pure fractal windows of width 2n+1; emits candidates confirmed at the
    close of the n-th candle after the pivot."""

    def __init__(self, n: int, atr_period: int = 14) -> None:
        if n < 1:
            raise ValueError("swing window n must be >= 1")
        self.n = n
        self._window: deque[Candle] = deque(maxlen=2 * n + 1)
        # the ATR is maintained by every detector: validation B and the
        # ready flag (règle 5) need it even when min_leg() is None.
        self.atr = WilderAtr(atr_period)

    @property
    def ready(self) -> bool:
        return self.atr.ready and len(self._window) == self._window.maxlen

    def min_leg(self) -> Decimal | None:
        return None  # pure fractal: no amplitude filter

    def update(self, candle: Candle) -> list[SwingEvent]:
        self.atr.update(candle)
        self._window.append(candle)
        if len(self._window) < 2 * self.n + 1:
            return []
        candles = list(self._window)
        center = candles[self.n]
        before = candles[: self.n]
        after = candles[self.n + 1 :]
        confirmed_at = candle.close_time
        events: list[SwingEvent] = []
        if all(center.high > c.high for c in before) and all(center.high >= c.high for c in after):
            events.append(SwingEvent(SwingKind.HIGH, center.high, center.open_time, confirmed_at))
        if all(center.low < c.low for c in before) and all(center.low <= c.low for c in after):
            events.append(SwingEvent(SwingKind.LOW, center.low, center.open_time, confirmed_at))
        return events


class AtrSwingDetector(FractalSwingDetector):
    """Fractal candidates + minimum leg amplitude of ATR x multiplier
    (docs/06 §11, règle 2 — see module docstring for the exact semantics;
    the amplitude check itself is applied by SwingSequence.push, which
    knows the last confirmed opposite swing)."""

    def __init__(self, n: int, atr_multiplier: Decimal, atr_period: int = 14) -> None:
        super().__init__(n, atr_period)
        if atr_multiplier <= 0:
            raise ValueError("atr_multiplier must be > 0")
        self.atr_multiplier = atr_multiplier

    def min_leg(self) -> Decimal | None:
        value = self.atr.value
        return None if value is None else value * self.atr_multiplier


class SequenceAction(StrEnum):
    APPENDED = "APPENDED"
    REPLACED = "REPLACED"
    REJECTED = "REJECTED"


class SwingSequence:
    """The alternating (zigzag) sequence of kept swings — the single source
    the structure state derives from (règles 1 et 3)."""

    def __init__(self) -> None:
        self.swings: list[SwingEvent] = []

    def last(self, kind: SwingKind) -> SwingEvent | None:
        for swing in reversed(self.swings):
            if swing.kind is kind:
                return swing
        return None

    def push(self, candidate: SwingEvent, min_leg: Decimal | None) -> SequenceAction:
        """Apply alternation and (for the ATR variant) the minimum-leg
        filter. A REJECTED candidate disappears for good (règle 2)."""
        last = self.swings[-1] if self.swings else None
        if last is not None and last.kind is candidate.kind:
            # same kind: keep the extreme (règle 1)
            more_extreme = (
                candidate.price > last.price
                if candidate.kind is SwingKind.HIGH
                else candidate.price < last.price
            )
            if not more_extreme:
                return SequenceAction.REJECTED
            self.swings[-1] = candidate
            return SequenceAction.REPLACED
        # opposite kind: a new leg — the ATR variant requires its amplitude,
        # measured from the last kept opposite swing (règle 2); the very
        # first swing has nothing to measure from and bootstraps the sequence
        if min_leg is not None and last is not None:
            if abs(candidate.price - last.price) < min_leg:
                return SequenceAction.REJECTED
        self.swings.append(candidate)
        return SequenceAction.APPENDED

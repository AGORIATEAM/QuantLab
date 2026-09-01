"""Structure state from the swing sequence — and from nothing else
(docs/06 §13, §15-§17 ; règle 3 : BOS/CHoCH are emitted events, never
state mutators, §23).

Labels (§13, equality resolved explicitly): current high > previous high →
HH else LH ; current low > previous low → HL else LL (EQUAL_* is §14, out
of the minimal scope). State (§15-§16), derived from the LAST label of
each kind once two pairs of swings exist:

    HH + HL → BULLISH        LH + LL → BEARISH        mixed → NEUTRAL

Transitions are total: any state can move to any of the three on the next
sequence mutation; before two pairs the state is UNKNOWN.
"""

from __future__ import annotations

from enum import StrEnum

from quantlab.structure.swings import SwingEvent, SwingKind


class StructureState(StrEnum):
    UNKNOWN = "UNKNOWN"
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class SwingLabel(StrEnum):
    HH = "HH"
    HL = "HL"
    LH = "LH"
    LL = "LL"


def label_last(swings: list[SwingEvent], kind: SwingKind) -> SwingLabel | None:
    """Label of the most recent swing of `kind` against the previous one of
    the same kind; None until two of that kind exist."""
    same = [s for s in swings if s.kind is kind]
    if len(same) < 2:
        return None
    current, previous = same[-1], same[-2]
    if kind is SwingKind.HIGH:
        return SwingLabel.HH if current.price > previous.price else SwingLabel.LH
    return SwingLabel.HL if current.price > previous.price else SwingLabel.LL


def derive_state(swings: list[SwingEvent]) -> StructureState:
    high_label = label_last(swings, SwingKind.HIGH)
    low_label = label_last(swings, SwingKind.LOW)
    if high_label is None or low_label is None:
        return StructureState.UNKNOWN
    if high_label is SwingLabel.HH and low_label is SwingLabel.HL:
        return StructureState.BULLISH
    if high_label is SwingLabel.LH and low_label is SwingLabel.LL:
        return StructureState.BEARISH
    return StructureState.NEUTRAL

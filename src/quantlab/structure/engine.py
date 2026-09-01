"""Market Structure Engine — minimal scope for H1 (docs/06 §8-§26,
§48-§50, §55-§56; ADR-0002).

Pure consumer of ReplayEvents: no repository, no clock — time only ever
comes from the candles. One fully independent state per SeriesKey (§48):
the 5m stream can never touch the 1h structure.

Readiness (règle 5): a series is `ready` once its ATR is warm AND the
fractal window is full AND the alternating sequence holds two pairs of
swings (two highs and two lows — both labels defined). The engine emits
NO StructureEvent before ready — warm-up seeding is internal; the first
emission is the initial STATE snapshot.

Every event carries engine_version + config_version (§42/§77),
event_timestamp and available_at (§56): a consumer replaying candles can
never see anything before the close that made it knowable (§55).

State changes come exclusively from the swing sequence (règle 3): breaks
are emitted alongside, never fed back.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from quantlab.data.replay import ReplayEvent, SeriesKey
from quantlab.structure.breaks import BreakDetector, BreakEvent, ValidationMethod
from quantlab.structure.state import StructureState, derive_state
from quantlab.structure.swings import (
    AtrSwingDetector,
    FractalSwingDetector,
    SequenceAction,
    SwingEvent,
    SwingKind,
    SwingSequence,
)

ENGINE_VERSION = "0.1.0"


class DetectorKind(StrEnum):
    FRACTAL = "fractal"
    ATR = "atr"


@dataclass(frozen=True)
class StructureConfig:
    detector: DetectorKind
    n: int
    atr_period: int = 14
    atr_multiplier: Decimal = Decimal("2")  # ATR detector only
    validation: ValidationMethod = ValidationMethod.CLOSE
    breakout_buffer: Decimal = Decimal(0)  # ATR multiples, validation B only

    @property
    def config_version(self) -> str:
        canonical = (
            f"qlsc-v1|{self.detector.value}|{self.n}|{self.atr_period}"
            f"|{self.atr_multiplier}|{self.validation.value}|{self.breakout_buffer}"
        )
        return hashlib.sha256(canonical.encode()).hexdigest()[:12]


class StructureEventType(StrEnum):
    SWING_CONFIRMED = "SWING_CONFIRMED"
    STATE = "STATE"
    STRUCTURE_BREAK = "STRUCTURE_BREAK"


@dataclass(frozen=True)
class StructureEvent:
    series: SeriesKey
    event_type: StructureEventType
    event_timestamp: datetime
    available_at: datetime
    engine_version: str
    config_version: str
    state: StructureState
    swing: SwingEvent | None = None
    brk: BreakEvent | None = None


@dataclass
class _SeriesRuntime:
    detector: FractalSwingDetector
    breaks: BreakDetector
    sequence: SwingSequence = field(default_factory=SwingSequence)
    state: StructureState = StructureState.UNKNOWN
    announced: bool = False  # first STATE snapshot emitted once ready

    @property
    def has_two_pairs(self) -> bool:
        highs = sum(1 for s in self.sequence.swings if s.kind is SwingKind.HIGH)
        lows = len(self.sequence.swings) - highs
        return highs >= 2 and lows >= 2

    @property
    def ready(self) -> bool:
        return self.detector.ready and self.has_two_pairs


class MarketStructureEngine:
    """Feed it every ReplayEvent (warm-up included — that is what seeds it);
    it returns the StructureEvents that became knowable at that candle."""

    def __init__(self, config: StructureConfig) -> None:
        self.config = config
        self._series: dict[SeriesKey, _SeriesRuntime] = {}

    def runtime(self, series: SeriesKey) -> _SeriesRuntime:
        runtime = self._series.get(series)
        if runtime is None:
            if self.config.detector is DetectorKind.ATR:
                detector: FractalSwingDetector = AtrSwingDetector(
                    self.config.n, self.config.atr_multiplier, self.config.atr_period
                )
            else:
                detector = FractalSwingDetector(self.config.n, self.config.atr_period)
            runtime = _SeriesRuntime(
                detector=detector,
                breaks=BreakDetector(self.config.validation, self.config.breakout_buffer),
            )
            self._series[series] = runtime
        return runtime

    def state_of(self, series: SeriesKey) -> StructureState:
        runtime = self._series.get(series)
        if runtime is None or not runtime.ready:
            return StructureState.UNKNOWN
        return runtime.state

    def on_event(self, event: ReplayEvent) -> list[StructureEvent]:
        runtime = self.runtime(event.series)
        candle = event.candle
        out: list[StructureEvent] = []

        # 1. swings confirmed at this close → sequence (alternation + ATR leg
        #    filter) → state, the single state source (règle 3)
        state_changed = False
        for candidate in runtime.detector.update(candle):
            action = runtime.sequence.push(candidate, runtime.detector.min_leg())
            if action is SequenceAction.REJECTED:
                continue
            runtime.breaks.arm(runtime.sequence.swings[-1])  # new/moved level (règle 4)
            new_state = derive_state(runtime.sequence.swings)
            if new_state is not runtime.state:
                runtime.state = new_state
                state_changed = True
            if runtime.ready and runtime.announced:
                out.append(self._emit(event, StructureEventType.SWING_CONFIRMED, swing=candidate))

        # 2. readiness gate (règle 5): nothing is emitted before ready; the
        #    first emission is the state snapshot
        if not runtime.ready:
            return []
        if not runtime.announced:
            runtime.announced = True
            return [self._emit(event, StructureEventType.STATE)]
        if state_changed:
            out.append(self._emit(event, StructureEventType.STATE))

        # 3. breaks at this close — events only, never state mutators
        for brk in runtime.breaks.update(candle, runtime.state, runtime.detector.atr.value):
            out.append(self._emit(event, StructureEventType.STRUCTURE_BREAK, brk=brk))
        return out

    def _emit(
        self,
        event: ReplayEvent,
        event_type: StructureEventType,
        swing: SwingEvent | None = None,
        brk: BreakEvent | None = None,
    ) -> StructureEvent:
        runtime = self._series[event.series]
        close = event.candle.close_time
        return StructureEvent(
            series=event.series,
            event_type=event_type,
            event_timestamp=close,
            available_at=close,
            engine_version=ENGINE_VERSION,
            config_version=self.config.config_version,
            state=runtime.state,
            swing=swing,
            brk=brk,
        )

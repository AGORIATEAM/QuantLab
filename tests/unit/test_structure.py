"""Market Structure Engine: hand-built golden cases (docs/06 §47) for
swings, alternation, ATR legs, state machine, breaks, readiness, and the
anti-look-ahead invariant against the replay."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fakes import (
    InMemoryCandles,
    InMemoryDatasets,
    InMemoryQualityEvents,
    InMemorySnapshotFactory,
    RecordingAudit,
)

from quantlab.core.clock import SimulatedClock
from quantlab.core.ids import new_id
from quantlab.data.datasets import SeriesResolver, freeze_dataset
from quantlab.data.replay import ReplayEvent, SeriesKey, replay_candles
from quantlab.domain.models import Candle, DatasetSeries, Instrument, Timeframe, Venue
from quantlab.structure.atr import WilderAtr
from quantlab.structure.breaks import (
    BreakDetector,
    BreakKind,
    ValidationMethod,
)
from quantlab.structure.engine import (
    ENGINE_VERSION,
    DetectorKind,
    MarketStructureEngine,
    StructureConfig,
    StructureEventType,
)
from quantlab.structure.state import StructureState, derive_state
from quantlab.structure.swings import (
    FractalSwingDetector,
    SequenceAction,
    SwingEvent,
    SwingKind,
    SwingSequence,
)

TF = Timeframe.H1
T0 = datetime(2026, 8, 1, 0, 0, tzinfo=UTC)

VENUE = Venue(venue_id=new_id(), code="BINANCE", name="Binance", venue_type="spot")
BTC = Instrument(
    instrument_id=new_id(),
    venue_id=VENUE.venue_id,
    asset_id=None,
    venue_symbol="BTCUSDT",
    instrument_type="spot",
    tick_size=Decimal("0.01"),
    lot_size=Decimal("0.00001"),
)
KEY_1H = SeriesKey(venue="BINANCE", venue_symbol="BTCUSDT", timeframe=TF, source="binance")
KEY_5M = SeriesKey(
    venue="BINANCE", venue_symbol="BTCUSDT", timeframe=Timeframe.M5, source="binance"
)


def candle(i: int, high: str, low: str, close: str | None = None, tf: Timeframe = TF) -> Candle:
    h, lo = Decimal(high), Decimal(low)
    c = (h + lo) / 2 if close is None else Decimal(close)
    open_time = T0 + i * tf.duration
    return Candle(
        candle_id=new_id(),
        instrument_id=BTC.instrument_id,
        timeframe=tf,
        open_time=open_time,
        close_time=open_time + tf.duration,
        open=(h + lo) / 2,
        high=h,
        low=lo,
        close=c,
        volume=Decimal("1"),
        source="binance",
    )


def events_for(candles: list[Candle], key: SeriesKey = KEY_1H) -> list[ReplayEvent]:
    return [ReplayEvent(candle=c, is_warmup=False, series=key) for c in candles]


def swing(kind: SwingKind, price: str, i: int = 0) -> SwingEvent:
    return SwingEvent(
        kind=kind,
        price=Decimal(price),
        pivot_timestamp=T0 + i * TF.duration,
        confirmation_timestamp=T0 + (i + 1) * TF.duration,
    )


# --- ATR -------------------------------------------------------------------


def test_wilder_atr_golden() -> None:
    atr = WilderAtr(period=3)
    assert atr.update(candle(0, "10", "8", "9")) is None  # TR=2
    assert atr.update(candle(1, "11", "9", "9")) is None  # TR=max(2,2,0)=2
    assert atr.update(candle(2, "10", "8", "9")) == Decimal("2")  # TR=2 -> SMA=2
    # next TR=5 (high 14, prev close 9): atr = (2*2 + 5) / 3 = 3
    assert atr.update(candle(3, "14", "9", "10")) == Decimal("3")
    assert atr.ready


# --- swings ----------------------------------------------------------------


def test_fractal_swing_confirmed_n_candles_after_pivot() -> None:
    detector = FractalSwingDetector(n=2, atr_period=2)
    rows = [
        candle(0, "1", "0.5"),
        candle(1, "2", "1.5"),
        candle(2, "5", "4"),  # pivot high
        candle(3, "3", "2.5"),
        candle(4, "2", "1.5"),  # confirming candle
    ]
    emitted: list[SwingEvent] = []
    for i, c in enumerate(rows):
        out = detector.update(c)
        if i < 4:
            assert out == []  # nothing knowable before the confirming close
        emitted.extend(out)
    assert [s.kind for s in emitted] == [SwingKind.HIGH]
    assert emitted[0].price == Decimal("5")
    assert emitted[0].pivot_timestamp == rows[2].open_time
    assert emitted[0].confirmation_timestamp == rows[4].close_time


def test_alternation_keeps_the_extreme_golden() -> None:
    seq = SwingSequence()
    assert seq.push(swing(SwingKind.HIGH, "100", 0), None) is SequenceAction.APPENDED
    # same kind, more extreme -> replaces
    assert seq.push(swing(SwingKind.HIGH, "105", 2), None) is SequenceAction.REPLACED
    # same kind, less extreme -> disappears
    assert seq.push(swing(SwingKind.HIGH, "103", 4), None) is SequenceAction.REJECTED
    assert seq.push(swing(SwingKind.LOW, "90", 6), None) is SequenceAction.APPENDED
    assert [(s.kind, s.price) for s in seq.swings] == [
        (SwingKind.HIGH, Decimal("105")),
        (SwingKind.LOW, Decimal("90")),
    ]  # always alternating


def test_atr_min_leg_measured_from_last_opposite_swing() -> None:
    seq = SwingSequence()
    min_leg = Decimal("10")
    assert seq.push(swing(SwingKind.LOW, "100", 0), min_leg) is SequenceAction.APPENDED  # bootstrap
    # leg of 5 < 10: candidate disappears for good (règle 2)
    assert seq.push(swing(SwingKind.HIGH, "105", 2), min_leg) is SequenceAction.REJECTED
    # a later candidate is measured from the SURVIVING low, not the rejected one
    assert seq.push(swing(SwingKind.HIGH, "115", 4), min_leg) is SequenceAction.APPENDED
    assert [(s.kind, s.price) for s in seq.swings] == [
        (SwingKind.LOW, Decimal("100")),
        (SwingKind.HIGH, Decimal("115")),
    ]


# --- state -----------------------------------------------------------------


def test_state_from_swing_sequence_golden() -> None:
    bullish = [
        swing(SwingKind.LOW, "90", 0),
        swing(SwingKind.HIGH, "100", 2),
        swing(SwingKind.LOW, "95", 4),  # HL
        swing(SwingKind.HIGH, "110", 6),  # HH
    ]
    assert derive_state(bullish) is StructureState.BULLISH
    neutral = [*bullish, swing(SwingKind.LOW, "85", 8)]  # LL with last HH -> mixed
    assert derive_state(neutral) is StructureState.NEUTRAL
    bearish = [*neutral, swing(SwingKind.HIGH, "105", 10)]  # LH + LL
    assert derive_state(bearish) is StructureState.BEARISH
    assert derive_state(bullish[:3]) is StructureState.UNKNOWN  # one pair only


# --- breaks ----------------------------------------------------------------


def test_bos_validation_close_vs_atr_buffer() -> None:
    close_rule = BreakDetector(ValidationMethod.CLOSE)
    buffered = BreakDetector(ValidationMethod.ATR_BUFFER, breakout_buffer=Decimal("0.1"))
    for detector in (close_rule, buffered):
        detector.arm(swing(SwingKind.HIGH, "100"))
    # close 100.5, ATR 10 -> buffer threshold 101: A validates, B does not
    breaking = candle(0, "101.5", "99", "100.5")
    a = close_rule.update(breaking, StructureState.BULLISH, Decimal("10"))
    b = buffered.update(breaking, StructureState.BULLISH, Decimal("10"))
    assert [e.kind for e in a] == [BreakKind.BOS]
    assert [e.kind for e in b] == [BreakKind.WICK_BREAK]  # wick beyond, close inside buffer


def test_wick_break_is_separate_and_does_not_consume_the_level() -> None:
    detector = BreakDetector(ValidationMethod.CLOSE)
    detector.arm(swing(SwingKind.HIGH, "100"))
    wick = detector.update(candle(0, "101", "98", "99.5"), StructureState.BULLISH, None)
    assert [e.kind for e in wick] == [BreakKind.WICK_BREAK]
    # second wick on the same armed swing: not re-recorded
    assert detector.update(candle(1, "101", "98", "99.5"), StructureState.BULLISH, None) == []
    # the level was NOT consumed: a close through it is still a BOS
    bos = detector.update(candle(2, "102", "99", "101"), StructureState.BULLISH, None)
    assert [e.kind for e in bos] == [BreakKind.BOS]
    assert bos[0].event_timestamp == bos[0].available_at


def test_a_level_breaks_exactly_once_until_a_new_swing_arms_it() -> None:
    detector = BreakDetector(ValidationMethod.CLOSE)
    detector.arm(swing(SwingKind.HIGH, "100"))
    first = detector.update(candle(0, "102", "99", "101"), StructureState.BULLISH, None)
    assert [e.kind for e in first] == [BreakKind.BOS]
    # N further closes above the same level -> zero further events (règle 4)
    for i in range(1, 6):
        assert detector.update(candle(i, "103", "100.5", "102"), StructureState.BULLISH, None) == []
    # a NEW confirmed swing re-arms the side
    detector.arm(swing(SwingKind.HIGH, "103", 6))
    again = detector.update(candle(7, "105", "102", "104"), StructureState.BULLISH, None)
    assert [e.kind for e in again] == [BreakKind.BOS]


def test_break_kind_depends_on_dominant_structure() -> None:
    up = candle(0, "102", "99", "101")
    for state, expected in [
        (StructureState.BULLISH, BreakKind.BOS),
        (StructureState.BEARISH, BreakKind.CHOCH),
        (StructureState.NEUTRAL, BreakKind.BREAK_UNCLASSIFIED),  # §18: no dominant structure
        (StructureState.UNKNOWN, BreakKind.BREAK_UNCLASSIFIED),
    ]:
        detector = BreakDetector(ValidationMethod.CLOSE)
        detector.arm(swing(SwingKind.HIGH, "100"))
        events = detector.update(up, state, None)
        assert [e.kind for e in events] == [expected], state


# --- engine ----------------------------------------------------------------

CONFIG = StructureConfig(detector=DetectorKind.FRACTAL, n=1, atr_period=2)

# n=1, atr_period=2 golden path to BULLISH (see each pivot in comments):
BULLISH_PATH = [
    candle(0, "10", "9", "9"),
    candle(1, "9.5", "8", "9"),  # pivot LOW 8
    candle(2, "11", "9", "10"),  # confirms LOW(8); pivot HIGH 11
    candle(3, "10.5", "8.5", "9"),  # confirms HIGH(11); pivot LOW 8.5 (HL)
    candle(4, "12", "9", "11"),  # confirms LOW(8.5); pivot HIGH 12 (HH)
    candle(5, "11.5", "10", "11"),  # confirms HIGH(12) -> two pairs -> BULLISH
]


def run_engine(
    engine: MarketStructureEngine, candles: list[Candle], key: SeriesKey = KEY_1H
) -> list:  # list[StructureEvent]
    out = []
    for event in events_for(candles, key):
        out.extend(engine.on_event(event))
    return out


def test_engine_ready_gate_and_first_state_snapshot() -> None:
    engine = MarketStructureEngine(CONFIG)
    emitted = []
    for i, c in enumerate(BULLISH_PATH):
        out = engine.on_event(ReplayEvent(candle=c, is_warmup=False, series=KEY_1H))
        if i < 5:
            assert out == []  # règle 5: silent until ready
            assert engine.state_of(KEY_1H) is StructureState.UNKNOWN
        emitted.extend(out)
    assert [e.event_type for e in emitted] == [StructureEventType.STATE]
    assert emitted[0].state is StructureState.BULLISH
    assert emitted[0].engine_version == ENGINE_VERSION
    assert emitted[0].config_version == CONFIG.config_version
    assert engine.state_of(KEY_1H) is StructureState.BULLISH


def test_choch_emitted_without_mutating_state() -> None:
    engine = MarketStructureEngine(CONFIG)
    run_engine(engine, BULLISH_PATH)
    # collapse through the armed low (8.5) while structure is BULLISH:
    # no new swing on this candle -> the CHOCH is an event, the state holds
    crash = candle(6, "10", "7.5", "8")
    out = run_engine(engine, [crash])
    kinds = [(e.event_type, e.brk.kind if e.brk else None) for e in out]
    assert (StructureEventType.STRUCTURE_BREAK, BreakKind.CHOCH) in kinds
    assert all(e.event_type is not StructureEventType.STATE for e in out)
    assert engine.state_of(KEY_1H) is StructureState.BULLISH  # règle 3
    assert all(e.state is StructureState.BULLISH for e in out)


def test_engine_series_are_independent() -> None:
    engine = MarketStructureEngine(CONFIG)
    run_engine(engine, BULLISH_PATH, KEY_1H)
    assert engine.state_of(KEY_1H) is StructureState.BULLISH
    assert engine.state_of(KEY_5M) is StructureState.UNKNOWN
    five_minute = [
        candle(i, str(c.high), str(c.low), str(c.close), tf=Timeframe.M5)
        for i, c in enumerate(BULLISH_PATH)
    ]
    run_engine(engine, five_minute, KEY_5M)
    assert engine.state_of(KEY_5M) is StructureState.BULLISH
    assert engine.state_of(KEY_1H) is StructureState.BULLISH


def test_engine_deterministic() -> None:
    path = [*BULLISH_PATH, candle(6, "10", "7.5", "8"), candle(7, "9", "8", "8.5")]
    a = run_engine(MarketStructureEngine(CONFIG), path)
    b = run_engine(MarketStructureEngine(CONFIG), path)
    assert [(e.event_type, e.state, e.available_at) for e in a] == [
        (e.event_type, e.state, e.available_at) for e in b
    ]


def test_config_version_distinguishes_configs() -> None:
    base = StructureConfig(detector=DetectorKind.FRACTAL, n=2)
    same = StructureConfig(detector=DetectorKind.FRACTAL, n=2)
    other = StructureConfig(detector=DetectorKind.ATR, n=2, atr_multiplier=Decimal("1.5"))
    assert base.config_version == same.config_version
    assert base.config_version != other.config_version


def test_atr_engine_filters_small_legs() -> None:
    # same path, huge multiplier: legs never reach ATR x 50 -> single swing
    # keeps the sequence from ever holding two pairs -> never ready
    config = StructureConfig(
        detector=DetectorKind.ATR, n=1, atr_period=2, atr_multiplier=Decimal("50")
    )
    engine = MarketStructureEngine(config)
    assert run_engine(engine, BULLISH_PATH) == []
    assert engine.state_of(KEY_1H) is StructureState.UNKNOWN


# --- anti-look-ahead against the replay ------------------------------------


def test_no_structure_event_available_before_its_candle_closes() -> None:
    """Engine fed by the real replay: at every emission, nothing the engine
    produced is available after the simulated clock, and no swing enters the
    sequence before its confirmation candle has closed (docs/06 §55-§56)."""
    rows = []
    price = 100
    for i in range(48):  # two days of 1h with a wavy path -> plenty of swings
        price += (-1) ** (i // 3) * 2
        rows.append(candle(i, str(price + 3), str(price - 3), str(price)))
    live = InMemoryCandles()
    live.insert_many(rows)
    datasets = InMemoryDatasets()
    audit = RecordingAudit()
    freeze_dataset(
        live,
        datasets,
        audit,
        "st",
        "v1",
        [(VENUE, BTC)],
        [TF],
        T0,
        T0 + 48 * TF.duration,
        "binance",
    )

    class Resolver(SeriesResolver):
        def __init__(self) -> None:
            pass

        def __call__(self, series: DatasetSeries) -> tuple[Venue, Instrument]:
            return VENUE, BTC

    clock = SimulatedClock(T0)
    engine = MarketStructureEngine(StructureConfig(detector=DetectorKind.FRACTAL, n=2))
    n_duration = 2 * TF.duration
    seen = 0
    for event in replay_candles(
        InMemorySnapshotFactory(live),
        datasets,
        Resolver(),
        InMemoryQualityEvents(),
        audit,
        "st",
        "v1",
        clock,
    ):
        for structure_event in engine.on_event(event):
            seen += 1
            assert structure_event.available_at <= clock.now()
            if structure_event.swing is not None:
                lag = structure_event.swing.confirmation_timestamp
                lag -= structure_event.swing.pivot_timestamp
                assert lag >= n_duration  # confirmed n candles after the pivot
        for kept in engine.runtime(event.series).sequence.swings:
            assert kept.confirmation_timestamp <= clock.now()  # never a future pivot
    assert seen > 0  # the invariant was actually exercised


def test_rejected_configs() -> None:
    with pytest.raises(ValueError):
        FractalSwingDetector(n=0)
    with pytest.raises(ValueError):
        WilderAtr(period=0)

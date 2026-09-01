"""H1 simulator: the amended pessimistic fill model, golden cases."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from quantlab.core.ids import new_id
from quantlab.data.replay import ReplayEvent, SeriesKey
from quantlab.domain.models import Candle, Timeframe
from quantlab.research.baseline import FillModel
from quantlab.research.h1 import H1Config, H1Simulator
from quantlab.structure.breaks import BreakDirection, BreakEvent, BreakKind
from quantlab.structure.engine import StructureEvent, StructureEventType
from quantlab.structure.state import StructureState
from quantlab.structure.swings import SwingEvent, SwingKind

TF = Timeframe.M5
T0 = datetime(2026, 8, 1, 0, 0, tzinfo=UTC)
KEY_5M = SeriesKey(venue="BINANCE", venue_symbol="BTCUSDT", timeframe=TF, source="binance")
KEY_1H = SeriesKey(
    venue="BINANCE", venue_symbol="BTCUSDT", timeframe=Timeframe.H1, source="binance"
)
INSTRUMENT_ID = new_id()

# frictionless fill: prices tell the story; cost cases set real fees
FREE = FillModel(taker_fee=Decimal("0"), half_spread=Decimal("0"), initial_capital=Decimal("10000"))


@dataclass
class StubAtr:
    value: Decimal | None


@dataclass
class StubDetector:
    atr: StubAtr


class StubSequence:
    def __init__(self, low: Decimal | None, high: Decimal | None) -> None:
        self._low, self._high = low, high

    def last(self, kind: SwingKind) -> SwingEvent | None:
        price = self._low if kind is SwingKind.LOW else self._high
        if price is None:
            return None
        return SwingEvent(kind=kind, price=price, pivot_timestamp=T0, confirmation_timestamp=T0)


@dataclass
class StubRuntime:
    sequence: StubSequence
    detector: StubDetector


class StubEngine:
    """Duck-typed MarketStructureEngine for the simulator's read paths."""

    def __init__(
        self,
        state: StructureState = StructureState.BULLISH,
        low: Decimal | None = Decimal("95"),
        high: Decimal | None = Decimal("110"),
        atr: Decimal | None = Decimal("2"),
    ) -> None:
        self.state = state
        self._runtime = StubRuntime(StubSequence(low, high), StubDetector(StubAtr(atr)))

    def state_of(self, key: SeriesKey) -> StructureState:
        return self.state

    def runtime(self, key: SeriesKey) -> StubRuntime:
        return self._runtime


def candle(i: int, o: str, h: str, lo: str, c: str) -> Candle:
    open_time = T0 + i * TF.duration
    return Candle(
        candle_id=new_id(),
        instrument_id=INSTRUMENT_ID,
        timeframe=TF,
        open_time=open_time,
        close_time=open_time + TF.duration,
        open=Decimal(o),
        high=Decimal(h),
        low=Decimal(lo),
        close=Decimal(c),
        volume=Decimal("1"),
        source="binance",
    )


def bos(i: int, direction: BreakDirection = BreakDirection.BULLISH) -> list[StructureEvent]:
    when = T0 + (i + 1) * TF.duration
    return [
        StructureEvent(
            series=KEY_5M,
            event_type=StructureEventType.STRUCTURE_BREAK,
            event_timestamp=when,
            available_at=when,
            engine_version="test",
            config_version="test",
            state=StructureState.BULLISH,
            brk=BreakEvent(
                kind=BreakKind.BOS,
                direction=direction,
                level=Decimal("100"),
                break_price=Decimal("100"),
                reference_pivot=T0,
                event_timestamp=when,
                available_at=when,
            ),
        )
    ]


def choch(i: int, direction: BreakDirection) -> list[StructureEvent]:
    events = bos(i, direction)
    brk = events[0].brk
    assert brk is not None
    object.__setattr__(brk, "kind", BreakKind.CHOCH)
    return events


def make_sim(
    config: H1Config | None = None,
    fill: FillModel = FREE,
    engine_5m: StubEngine | None = None,
    engine_1h: StubEngine | None = None,
) -> tuple[H1Simulator, StubEngine, StubEngine]:
    e5 = engine_5m or StubEngine()
    e1 = engine_1h or StubEngine()
    config = config or H1Config(2, 3, Decimal("2"), Decimal("0"), Decimal("2"), Decimal("0"))
    sim = H1Simulator(config, e5, e1, KEY_5M, KEY_1H, fill)  # type: ignore[arg-type]
    return sim, e5, e1


def feed(sim: H1Simulator, rows: list[tuple[Candle, list[StructureEvent]]]) -> None:
    for c, events in rows:
        sim.on_5m(ReplayEvent(candle=c, is_warmup=False, series=KEY_5M), events)


def test_entry_at_next_open_stop_first_when_both_touched() -> None:
    # signal at candle 0 close (100); entry at candle 1 OPEN (100); stop 95
    # (last 5m low), target 2R = 110. Candle 2 touches BOTH 90 and 112:
    # the stop is deemed hit first (pessimistic) -> -1R.
    sim, _, _ = make_sim()
    feed(
        sim,
        [
            (candle(0, "99", "101", "98", "100"), bos(0)),
            (candle(1, "100", "104", "99", "103"), []),  # entry fills at open 100
            (candle(2, "103", "112", "90", "111"), []),  # both touched -> stop first
        ],
    )
    m = sim.metrics
    assert m.trades == 1
    assert m.wins == 0
    assert m.sum_r == Decimal("-1")  # exactly -1R at the stop, no costs


def test_target_reached_pays_r_multiple() -> None:
    sim, _, _ = make_sim()
    feed(
        sim,
        [
            (candle(0, "99", "101", "98", "100"), bos(0)),
            (candle(1, "100", "104", "99", "103"), []),  # entry 100, stop 95, target 110
            (candle(2, "103", "111", "102", "110"), []),  # target touched, stop untouched
        ],
    )
    assert sim.metrics.trades == 1
    assert sim.metrics.sum_r == Decimal("2")  # +2R clean


def test_gap_beyond_stop_fills_at_open_not_stop() -> None:
    sim, _, _ = make_sim()
    feed(
        sim,
        [
            (candle(0, "99", "101", "98", "100"), bos(0)),
            (candle(1, "100", "104", "99", "103"), []),  # entry 100, stop 95
            (candle(2, "90", "92", "88", "91"), []),  # opens straight through the stop
        ],
    )
    # loss = (100-90)/5 = 2R at the open, worse than the stop level
    assert sim.metrics.sum_r == Decimal("-2")


def test_min_stop_atr_skips_instead_of_widening() -> None:
    config = H1Config(2, 3, Decimal("2"), Decimal("0"), Decimal("2"), Decimal("0.5"))
    # stop distance at signal = 100 - 99.5 = 0.5 < 0.5 x ATR(2) = 1 -> skip
    sim, _, _ = make_sim(config, engine_5m=StubEngine(low=Decimal("99.5")))
    feed(
        sim,
        [
            (candle(0, "99", "101", "98", "100"), bos(0)),
            (candle(1, "100", "104", "99", "103"), []),
        ],
    )
    assert sim.metrics.trades == 0
    assert sim.metrics.skipped_min_stop == 1


def test_one_position_no_pyramiding_signals_ignored() -> None:
    sim, _, _ = make_sim()
    feed(
        sim,
        [
            (candle(0, "99", "101", "98", "100"), bos(0)),
            (candle(1, "100", "104", "99", "103"), bos(1)),  # in position: ignored
            (candle(2, "103", "105", "102", "104"), bos(2)),  # still ignored
        ],
    )
    assert sim.metrics.trades == 0  # position still open (neither stop nor target)
    assert sim.metrics.ignored_in_position == 2


def test_notional_capped_at_equity() -> None:
    # stop distance 0.1% of price -> uncapped size would be 5x equity
    sim, _, _ = make_sim(engine_5m=StubEngine(low=Decimal("99.9")))
    feed(
        sim,
        [
            (candle(0, "99", "101", "98", "100"), bos(0)),
            (candle(1, "100", "104", "99.95", "103"), []),
        ],
    )
    assert sim.metrics.capped == 1


def test_choch_against_position_exits_at_next_open() -> None:
    sim, _, _ = make_sim()
    feed(
        sim,
        [
            (candle(0, "99", "101", "98", "100"), bos(0)),
            (candle(1, "100", "104", "99", "103"), []),  # entry 100
            (candle(2, "103", "105", "102", "104"), choch(2, BreakDirection.BEARISH)),
            (candle(3, "102", "103", "101", "102"), []),  # exit fills at open 102
        ],
    )
    m = sim.metrics
    assert m.trades == 1
    assert m.sum_r == Decimal("0.4")  # (102-100)/5 R
    assert m.wins == 1


def test_no_entry_when_1h_neutral_or_direction_mismatch() -> None:
    sim, _, _ = make_sim(engine_1h=StubEngine(state=StructureState.NEUTRAL))
    feed(
        sim,
        [(candle(0, "99", "101", "98", "100"), bos(0)), (candle(1, "100", "101", "99", "100"), [])],
    )
    assert sim.metrics.trades == 0

    sim2, _, _ = make_sim(engine_1h=StubEngine(state=StructureState.BEARISH))
    feed(
        sim2,
        [(candle(0, "99", "101", "98", "100"), bos(0)), (candle(1, "100", "101", "99", "100"), [])],
    )
    assert sim2.metrics.trades == 0  # bullish BOS against bearish context


def test_costs_reported_in_r() -> None:
    fill = FillModel(
        taker_fee=Decimal("0.001"), half_spread=Decimal("0.0001"), initial_capital=Decimal("10000")
    )
    sim, _, _ = make_sim(fill=fill)
    feed(
        sim,
        [
            (candle(0, "99", "101", "98", "100"), bos(0)),
            (candle(1, "100", "104", "99", "103"), []),
            (candle(2, "103", "112", "102", "111"), []),  # target hit
        ],
    )
    m = sim.metrics
    assert m.trades == 1
    assert m.fees_paid > 0
    assert m.sum_cost_r > Decimal("0.04")  # ~0.22% costs on a 5% stop ≈ 0.044 R
    assert m.sum_r < Decimal("2")  # costs eat into the clean 2R

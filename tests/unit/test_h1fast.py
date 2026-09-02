"""ADR-0003 fast path: miniature equivalence against the Decimal reference
(engines + simulator) on a synthetic multi-timeframe stream, plus the
determinism requirement."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from quantlab.core.ids import new_id
from quantlab.data.replay import ReplayEvent, SeriesKey
from quantlab.domain.models import Candle, Instrument, Timeframe
from quantlab.research.baseline import FillModel
from quantlab.research.fast.equivalence import (
    LoggingSimulator,
    compare_trade_logs,
    rel_equal,
)
from quantlab.research.fast.h1fast import FastSimulator, FastStructure, run_shard
from quantlab.research.h1 import H1Config
from quantlab.structure.engine import MarketStructureEngine

T0 = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
INSTRUMENT = Instrument(
    instrument_id=new_id(),
    venue_id=new_id(),
    asset_id=None,
    venue_symbol="BTCUSDT",
    instrument_type="spot",
    tick_size=Decimal("0.01"),
    lot_size=Decimal("0.00001"),
)
KEY_5M = SeriesKey(
    venue="BINANCE", venue_symbol="BTCUSDT", timeframe=Timeframe.M5, source="binance"
)
KEY_1H = SeriesKey(
    venue="BINANCE", venue_symbol="BTCUSDT", timeframe=Timeframe.H1, source="binance"
)


def synthetic_rows(hours: int = 480) -> list[tuple[bool, bool, int, float, float, float, float]]:
    """Deterministic block-trend path (24h up / 24h down with hourly wobble
    and 5m noise, 2-decimal prices) in the replay's availability order.
    Long enough for the 1h context to become ready and flip states — the
    fast/slow pair trades on it (>3 trades at 480h)."""
    rows: list[tuple[bool, bool, int, float, float, float, float]] = []
    price = 10_000.0
    for hour in range(hours):
        direction = 1 if (hour // 24) % 2 == 0 else -1
        wobble = ((hour * 7) % 5 - 2) * 8
        drift = direction * 40 + wobble
        hour_open = price
        hour_high = hour_low = price
        for minute5 in range(12):
            i = hour * 12 + minute5
            noise = ((i * 37) % 7 - 3) * 3
            o = round(price, 2)
            c = round(price + drift / 12 + noise, 2)
            h = round(max(o, c) + 1.5 + abs(noise) / 2, 2)
            lo = round(min(o, c) - 1.5 - abs(noise) / 3, 2)
            ots = int((T0 + i * timedelta(minutes=5)).timestamp())
            rows.append((True, False, ots, o, h, lo, c))
            hour_high = max(hour_high, h)
            hour_low = min(hour_low, lo)
            price = c
        hots = int((T0 + hour * timedelta(hours=1)).timestamp())
        rows.append(
            (
                False,
                False,
                hots,
                round(hour_open, 2),
                round(hour_high, 2),
                round(hour_low, 2),
                round(price, 2),
            )
        )
    return rows


def to_candle(row: tuple[bool, bool, int, float, float, float, float]) -> Candle:
    is_5m, _w, ots, o, h, lo, c = row
    tf = Timeframe.M5 if is_5m else Timeframe.H1
    open_time = datetime.fromtimestamp(ots, tz=UTC)
    return Candle(
        candle_id=new_id(),
        instrument_id=INSTRUMENT.instrument_id,
        timeframe=tf,
        open_time=open_time,
        close_time=open_time + tf.duration,
        open=Decimal(str(o)),
        high=Decimal(str(h)),
        low=Decimal(str(lo)),
        close=Decimal(str(c)),
        volume=Decimal("1"),
        source="binance",
    )


CONFIG = H1Config(2, 3, Decimal("1.5"), Decimal("0"), Decimal("2"), Decimal("0"))


def run_slow(rows: list) -> tuple[LoggingSimulator, MarketStructureEngine]:
    engine_5m = MarketStructureEngine(CONFIG.engine_config(CONFIG.n_5m))
    engine_1h = MarketStructureEngine(CONFIG.engine_config(CONFIG.n_1h))
    sim = LoggingSimulator(CONFIG, engine_5m, engine_1h, KEY_5M, KEY_1H, FillModel())
    for row in rows:
        candle = to_candle(row)
        if row[0]:
            event = ReplayEvent(candle=candle, is_warmup=False, series=KEY_5M)
            sim.on_5m(event, engine_5m.on_event(event))
        else:
            engine_1h.on_event(ReplayEvent(candle=candle, is_warmup=False, series=KEY_1H))
    sim.finalize()
    return sim, engine_5m


def run_fast(rows: list) -> FastSimulator:
    s5 = FastStructure(CONFIG.n_5m, 1.5, 0.0)
    s1 = FastStructure(CONFIG.n_1h, 1.5, 0.0)
    sim = FastSimulator(2.0, 0.0, s5, s1, log_trades=True)
    for is_5m, warmup, ots, o, h, lo, c in rows:
        if is_5m:
            sim.on_5m(warmup, ots, o, h, lo, c, s5.update(o, h, lo, c))
        else:
            s1.update(o, h, lo, c)
    sim.finalize()
    return sim


def test_fast_reproduces_decimal_reference_trade_by_trade() -> None:
    rows = synthetic_rows(480)
    slow, _ = run_slow(rows)
    fast = run_fast(rows)

    assert slow.metrics.trades > 3  # the scenario actually trades
    diffs = compare_trade_logs(slow.trade_log, fast.trade_log or [], "mini")
    assert diffs == [], diffs[:5]
    assert slow.metrics.trades == fast.metrics.trades
    assert slow.metrics.capped == fast.metrics.capped
    assert slow.metrics.ignored_in_position == fast.metrics.ignored_in_position
    assert slow.metrics.skipped_min_stop == fast.metrics.skipped_min_stop
    assert rel_equal(float(slow.metrics.sum_r), fast.metrics.sum_r)
    assert rel_equal(float(slow.metrics.fees_paid), fast.metrics.fees_paid)
    assert rel_equal(float(slow.metrics.final_equity), fast.metrics.final_equity)
    assert slow.metrics.bars == fast.metrics.bars
    assert slow.metrics.bars_in_position == fast.metrics.bars_in_position


def test_fast_run_shard_is_deterministic() -> None:
    rows = synthetic_rows(240)
    configs = [
        (0, 2, 3, 1.5, 0.0, 2.0, 0.0),
        (1, 3, 5, 2.0, 0.1, 1.5, 0.5),
    ]
    a = run_shard(rows, configs, log_trades=True)
    b = run_shard(rows, configs, log_trades=True)
    assert [(i, m, t) for i, m, _c, t in a] == [(i, m, t) for i, m, _c, t in b]

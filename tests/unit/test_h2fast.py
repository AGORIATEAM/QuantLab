"""H2 (failed sweep) miniature equivalence: the Decimal reference
(H2Simulator over the real engines) versus the fast mirror on a synthetic
stream with periodic deep wicks — trade journals identical, the min_stop
filter actually bites, determinism holds."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from quantlab.core.ids import new_id
from quantlab.data.replay import ReplayEvent, SeriesKey
from quantlab.domain.models import Candle, Timeframe
from quantlab.research.baseline import FillModel
from quantlab.research.fast.equivalence import compare_trade_logs, rel_equal
from quantlab.research.fast.h1fast import FastStructure
from quantlab.research.fast.h2fast import TF_1H, TF_5M, FastH2Simulator, run_shard_h2
from quantlab.research.h1 import H1Config
from quantlab.research.h2 import H2LoggingSimulator
from quantlab.structure.engine import MarketStructureEngine

T0 = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
INSTRUMENT_ID = new_id()
KEY_5M = SeriesKey(
    venue="BINANCE", venue_symbol="BTCUSDT", timeframe=Timeframe.M5, source="binance"
)
KEY_1H = SeriesKey(
    venue="BINANCE", venue_symbol="BTCUSDT", timeframe=Timeframe.H1, source="binance"
)


def synthetic_rows(hours: int = 480) -> list[tuple[int, bool, int, float, float, float, float]]:
    """Block-trend path with a deep counter-trend wick every 17th 5m candle:
    the sweep scenario H2 trades on (33 trades at 480h, min_stop=0)."""
    rows: list[tuple[int, bool, int, float, float, float, float]] = []
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
            deep = 4.0 if (i % 17) == 0 else 0.0
            o = round(price, 2)
            c = round(price + drift / 12 + noise, 2)
            h = round(max(o, c) + 1.5 + abs(noise) / 2 + (deep if direction < 0 else 0), 2)
            lo = round(min(o, c) - 1.5 - abs(noise) / 3 - (deep if direction > 0 else 0), 2)
            ots = int((T0 + i * timedelta(minutes=5)).timestamp())
            rows.append((TF_5M, False, ots, o, h, lo, c))
            hour_high = max(hour_high, h)
            hour_low = min(hour_low, lo)
            price = c
        hots = int((T0 + hour * timedelta(hours=1)).timestamp())
        rows.append(
            (
                TF_1H,
                False,
                hots,
                round(hour_open, 2),
                round(hour_high, 2),
                round(hour_low, 2),
                round(price, 2),
            )
        )
    return rows


def to_candle(row: tuple[int, bool, int, float, float, float, float]) -> Candle:
    tf_idx, _w, ots, o, h, lo, c = row
    tf = Timeframe.M5 if tf_idx == TF_5M else Timeframe.H1
    open_time = datetime.fromtimestamp(ots, tz=UTC)
    return Candle(
        candle_id=new_id(),
        instrument_id=INSTRUMENT_ID,
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


def run_pair(min_stop: str) -> tuple[H2LoggingSimulator, FastH2Simulator]:
    rows = synthetic_rows(480)
    config = H1Config(2, 3, Decimal("1.5"), Decimal("0"), Decimal("2"), Decimal(min_stop))
    engine_5m = MarketStructureEngine(config.engine_config(2))
    engine_ctx = MarketStructureEngine(config.engine_config(3))
    slow = H2LoggingSimulator(config, engine_5m, engine_ctx, KEY_5M, KEY_1H, FillModel())
    for row in rows:
        candle = to_candle(row)
        if row[0] == TF_5M:
            event = ReplayEvent(candle=candle, is_warmup=False, series=KEY_5M)
            slow.on_5m(event, engine_5m.on_event(event))
        else:
            engine_ctx.on_event(ReplayEvent(candle=candle, is_warmup=False, series=KEY_1H))
    slow.finalize()

    s5 = FastStructure(2, 1.5, 0.0)
    sc = FastStructure(3, 1.5, 0.0)
    fast = FastH2Simulator(2.0, float(min_stop), s5, sc, log_trades=True)
    for tf_idx, warmup, ots, o, h, lo, c in rows:
        if tf_idx == TF_5M:
            fast.on_5m(warmup, ots, o, h, lo, c, s5.update(o, h, lo, c))
        else:
            sc.update(o, h, lo, c)
    fast.finalize()
    return slow, fast


def test_h2_fast_reproduces_decimal_reference_trade_by_trade() -> None:
    slow, fast = run_pair("0")
    assert slow.metrics.trades > 10  # the sweep scenario actually trades
    diffs = compare_trade_logs(slow.trade_log, fast.trade_log or [], "h2-mini")
    assert diffs == [], diffs[:5]
    assert slow.metrics.trades == fast.metrics.trades
    assert slow.metrics.ignored_in_position == fast.metrics.ignored_in_position
    assert slow.metrics.skipped_min_stop == fast.metrics.skipped_min_stop == 0
    assert rel_equal(float(slow.metrics.sum_r), fast.metrics.sum_r)
    assert rel_equal(float(slow.metrics.final_equity), fast.metrics.final_equity)


def test_h2_min_stop_filter_bites_identically() -> None:
    slow, fast = run_pair("0.5")
    assert slow.metrics.skipped_min_stop > 5  # the wick-extreme stop is tight: it bites
    assert slow.metrics.skipped_min_stop == fast.metrics.skipped_min_stop
    assert slow.metrics.trades == fast.metrics.trades
    diffs = compare_trade_logs(slow.trade_log, fast.trade_log or [], "h2-ms")
    assert diffs == [], diffs[:5]


def test_h2_run_shard_deterministic() -> None:
    rows = synthetic_rows(240)
    configs = [
        (0, TF_1H, 2, 1, 1.5, 0.0, 2.0, 0.0),
        (1, TF_1H, 3, 0, 2.0, 0.1, 1.5, 0.3),
    ]
    a = run_shard_h2(rows, configs, log_trades=True)
    b = run_shard_h2(rows, configs, log_trades=True)
    assert [(i, m, t) for i, m, _c, t in a] == [(i, m, t) for i, m, _c, t in b]

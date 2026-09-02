"""H3 (noise-sized sweep) miniature equivalence: the Decimal reference
(H3Simulator over the real engines) versus the fast mirror on a synthetic
15m/4h stream with periodic deep wicks — trade journals identical, both
branches of max(wick, k x ATR) exercised, the k=0 degeneration to H2
(min_stop=0) holds, determinism holds. The Sharpe comparison pins the
15m day rule (BAR_SECONDS=900) against the slow close_time convention."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from quantlab.core.ids import new_id
from quantlab.data.replay import ReplayEvent, SeriesKey
from quantlab.domain.models import Candle, Timeframe
from quantlab.research.baseline import FillModel
from quantlab.research.fast.equivalence import compare_trade_logs, rel_equal
from quantlab.research.fast.h1fast import FastStructure
from quantlab.research.fast.h2fast import FastH2Simulator
from quantlab.research.fast.h3fast import TF_4H, TF_15M, FastH3Simulator, run_shard_h3
from quantlab.research.h1 import H1Config
from quantlab.research.h3 import H3LoggingSimulator
from quantlab.structure.engine import MarketStructureEngine

T0 = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
INSTRUMENT_ID = new_id()
KEY_15M = SeriesKey(
    venue="BINANCE", venue_symbol="BTCUSDT", timeframe=Timeframe.M15, source="binance"
)
KEY_4H = SeriesKey(
    venue="BINANCE", venue_symbol="BTCUSDT", timeframe=Timeframe.H4, source="binance"
)


def synthetic_rows(hours: int = 1920) -> list[tuple[int, bool, int, float, float, float, float]]:
    """Block-trend path (96h blocks) with a deep counter-trend wick every
    17th 15m candle and a very deep one every 51st: the sweep scenario H3
    trades on (85 trades at k=0, 64 at k=3 with both max() branches hit)."""
    rows: list[tuple[int, bool, int, float, float, float, float]] = []
    price = 10_000.0
    for hour in range(hours):
        direction = 1 if (hour // 96) % 2 == 0 else -1
        wobble = ((hour * 7) % 5 - 2) * 8
        drift = direction * 16 + wobble
        for q in range(4):
            i = hour * 4 + q
            noise = ((i * 37) % 7 - 3) * 4
            deep = 90.0 if i % 51 == 0 else (30.0 if i % 17 == 0 else 0.0)
            o = round(price, 2)
            c = round(price + drift / 4 + noise, 2)
            h = round(max(o, c) + 3 + abs(noise) / 2 + (deep if direction < 0 else 0), 2)
            lo = round(min(o, c) - 3 - abs(noise) / 3 - (deep if direction > 0 else 0), 2)
            ots = int((T0 + i * timedelta(minutes=15)).timestamp())
            rows.append((TF_15M, False, ots, o, h, lo, c))
            price = c
        if hour % 4 == 3:
            chunk = [r for r in rows if r[0] == TF_15M][-16:]
            rows.append(
                (
                    TF_4H,
                    False,
                    int((T0 + (hour - 3) * timedelta(hours=1)).timestamp()),
                    chunk[0][3],
                    max(r[4] for r in chunk),
                    min(r[5] for r in chunk),
                    chunk[-1][6],
                )
            )
    return rows


def to_candle(row: tuple[int, bool, int, float, float, float, float]) -> Candle:
    tf_idx, _w, ots, o, h, lo, c = row
    tf = Timeframe.M15 if tf_idx == TF_15M else Timeframe.H4
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


def run_pair(k_stop: str) -> tuple[H3LoggingSimulator, FastH3Simulator]:
    rows = synthetic_rows()
    config = H1Config(2, 3, Decimal("1.5"), Decimal("0"), Decimal("2"), Decimal("0"))
    engine_15m = MarketStructureEngine(config.engine_config(2))
    engine_ctx = MarketStructureEngine(config.engine_config(3))
    slow = H3LoggingSimulator(
        config, engine_15m, engine_ctx, KEY_15M, KEY_4H, FillModel(), k_stop=Decimal(k_stop)
    )
    for row in rows:
        candle = to_candle(row)
        if row[0] == TF_15M:
            event = ReplayEvent(candle=candle, is_warmup=False, series=KEY_15M)
            slow.on_5m(event, engine_15m.on_event(event))
        else:
            engine_ctx.on_event(ReplayEvent(candle=candle, is_warmup=False, series=KEY_4H))
    slow.finalize()

    s15 = FastStructure(2, 1.5, 0.0)
    sc = FastStructure(3, 1.5, 0.0)
    fast = FastH3Simulator(2.0, float(k_stop), s15, sc, log_trades=True)
    for tf_idx, warmup, ots, o, h, lo, c in rows:
        if tf_idx == TF_15M:
            fast.on_5m(warmup, ots, o, h, lo, c, s15.update(o, h, lo, c))
        else:
            sc.update(o, h, lo, c)
    fast.finalize()
    return slow, fast


def test_h3_fast_reproduces_decimal_reference_trade_by_trade() -> None:
    slow, fast = run_pair("3")
    assert slow.metrics.trades > 10  # the sweep scenario actually trades
    diffs = compare_trade_logs(slow.trade_log, fast.trade_log or [], "h3-mini")
    assert diffs == [], diffs[:5]
    assert slow.metrics.trades == fast.metrics.trades
    assert slow.metrics.ignored_in_position == fast.metrics.ignored_in_position
    # both branches of max(wick, k x ATR) exercised, counted identically
    assert 0 < fast.metrics.stop_atr_dominated < fast.metrics.trades
    assert slow.metrics.stop_atr_dominated == fast.metrics.stop_atr_dominated
    assert rel_equal(float(slow.metrics.sum_r), fast.metrics.sum_r)
    assert rel_equal(float(slow.metrics.final_equity), fast.metrics.final_equity)
    # pins BAR_SECONDS=900: daily equity day boundaries must match the slow side
    assert slow.metrics.sharpe_annualized is not None
    assert fast.metrics.sharpe_annualized is not None
    assert rel_equal(slow.metrics.sharpe_annualized, fast.metrics.sharpe_annualized)


def test_h3_k0_degenerates_to_h2_min_stop_zero() -> None:
    rows = synthetic_rows()

    def feed(sim_class: type[FastH2Simulator]) -> FastH2Simulator:
        s15 = FastStructure(2, 1.5, 0.0)
        sc = FastStructure(3, 1.5, 0.0)
        sim = sim_class(2.0, 0.0, s15, sc, log_trades=True)
        for tf_idx, warmup, ots, o, h, lo, c in rows:
            if tf_idx == TF_15M:
                sim.on_5m(warmup, ots, o, h, lo, c, s15.update(o, h, lo, c))
            else:
                sc.update(o, h, lo, c)
        sim.finalize()
        return sim

    h3 = feed(FastH3Simulator)
    h2 = feed(FastH2Simulator)
    assert h3.metrics.trades == h2.metrics.trades > 10
    assert h3.metrics.stop_atr_dominated == 0  # k=0: the wick always wins the max
    diffs = compare_trade_logs(h2.trade_log or [], h3.trade_log or [], "h3-k0")
    assert diffs == [], diffs[:5]


def test_h3_run_shard_deterministic() -> None:
    rows = synthetic_rows(960)
    configs = [
        (0, TF_4H, 2, 1, 2.0, 0.0, 2.0, 3.0),
        (1, TF_4H, 3, 0, 2.0, 0.1, 1.5, 4.0),
    ]
    a = run_shard_h3(rows, configs, log_trades=True)
    b = run_shard_h3(rows, configs, log_trades=True)
    assert [(i, m, t) for i, m, _c, t in a] == [(i, m, t) for i, m, _c, t in b]

"""H4 (value-located sweep) miniature equivalence: the Decimal reference
(H4Simulator + real profile engine) versus the fast mirror fed
extraction-style annotated rows — trade journals identical, LABEL PARITY
exact per trade, per-(side, bucket) counters exact, primary_ignored
exact, and the frozen invariant that H4 trades exactly like H3 (labels
never alter the population)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from test_h3fast import synthetic_rows

from quantlab.core.ids import new_id
from quantlab.data.replay import ReplayEvent, SeriesKey
from quantlab.domain.models import Candle, Timeframe
from quantlab.profile import VolumeProfileEngine
from quantlab.research.baseline import FillModel
from quantlab.research.fast.equivalence import compare_trade_logs, rel_equal
from quantlab.research.fast.extract import MultiRowH4
from quantlab.research.fast.h1fast import FastStructure
from quantlab.research.fast.h3fast import TF_4H, TF_15M, FastH3Simulator
from quantlab.research.fast.h4fast import FastH4Simulator, run_shard_h4
from quantlab.research.h1 import H1Config
from quantlab.research.h4 import H4LoggingSimulator
from quantlab.structure.engine import MarketStructureEngine

T0 = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
INSTRUMENT_ID = new_id()
KEY_15M = SeriesKey(
    venue="BINANCE", venue_symbol="BTCUSDT", timeframe=Timeframe.M15, source="binance"
)
KEY_4H = SeriesKey(
    venue="BINANCE", venue_symbol="BTCUSDT", timeframe=Timeframe.H4, source="binance"
)


def to_candle(row: tuple) -> Candle:
    tf_idx, _w, ots, o, h, lo, c = row[:7]
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


def annotate(rows: list[tuple]) -> list[MultiRowH4]:
    """Mirror of extract_rows_multi_h4 for the synthetic stream: the same
    Decimal profile engine builds the float prof tuples."""
    profiles = VolumeProfileEngine()
    out: list[MultiRowH4] = []
    for row in rows:
        tf_idx, warmup, ots, o, h, lo, c = row
        prof = None
        if tf_idx == TF_15M:
            candle = to_candle(row)
            profiles.on_event(ReplayEvent(candle=candle, is_warmup=warmup, series=KEY_15M))
            previous = profiles.previous(KEY_15M)
            if previous is not None and previous.day == candle.open_time.date() - timedelta(days=1):
                prof = (
                    float(previous.poc),
                    float(previous.vah),
                    float(previous.val),
                    float(previous.day_low),
                    float(previous.day_high),
                )
        out.append((tf_idx, warmup, ots, o, h, lo, c, prof))
    return out


def run_pair() -> tuple[H4LoggingSimulator, FastH4Simulator]:
    rows = synthetic_rows()
    config = H1Config(2, 3, Decimal("1.5"), Decimal("0"), Decimal("2"), Decimal("0"))
    engine_15m = MarketStructureEngine(config.engine_config(2))
    engine_ctx = MarketStructureEngine(config.engine_config(3))
    profiles = VolumeProfileEngine()
    slow = H4LoggingSimulator(
        config,
        engine_15m,
        engine_ctx,
        KEY_15M,
        KEY_4H,
        FillModel(),
        k_stop=Decimal("3"),
        profiles=profiles,
    )
    for row in rows:
        candle = to_candle(row)
        if row[0] == TF_15M:
            event = ReplayEvent(candle=candle, is_warmup=False, series=KEY_15M)
            profiles.on_event(event)  # fed BEFORE the simulator, as in the harness
            slow.on_5m(event, engine_15m.on_event(event))
        else:
            engine_ctx.on_event(ReplayEvent(candle=candle, is_warmup=False, series=KEY_4H))
    slow.finalize()

    s15 = FastStructure(2, 1.5, 0.0)
    sc = FastStructure(3, 1.5, 0.0)
    fast = FastH4Simulator(2.0, 3.0, s15, sc, log_trades=True)
    for tf_idx, warmup, ots, o, h, lo, c, prof in annotate(rows):
        if tf_idx == TF_15M:
            fast.prof = prof
            fast.on_5m(warmup, ots, o, h, lo, c, s15.update(o, h, lo, c))
        else:
            sc.update(o, h, lo, c)
    fast.finalize()
    return slow, fast


def test_h4_fast_reproduces_decimal_reference_with_labels() -> None:
    slow, fast = run_pair()
    assert slow.metrics.trades > 10
    diffs = compare_trade_logs(slow.trade_log, fast.trade_log or [], "h4-mini")
    assert diffs == [], diffs[:5]
    # LABEL PARITY: exact (side, bucket) per closed trade, same order
    assert slow.label_log == fast.label_log
    assert len(slow.label_log) == slow.metrics.trades
    # the stream actually exercises the partition
    assert len(set(slow.label_log)) >= 4
    primary = sum(
        1
        for side, bucket in slow.label_log
        if (side > 0 and bucket == 3) or (side < 0 and bucket == 4)
    )
    assert primary > 0
    assert slow.primary_ignored == fast.primary_ignored > 0
    for key, s_stats in slow.bucket_stats.items():
        f_stats = fast.bucket_stats[key]
        assert (s_stats.trades, s_stats.wins, s_stats.dominated) == (
            f_stats.trades,
            f_stats.wins,
            f_stats.dominated,
        ), key
        assert rel_equal(float(s_stats.sum_r), f_stats.sum_r), key
        assert rel_equal(float(s_stats.pos_r), f_stats.pos_r), key
        assert rel_equal(float(s_stats.neg_r), f_stats.neg_r), key
        assert rel_equal(float(s_stats.sum_cost_r), f_stats.sum_cost_r), key


def test_h4_trades_exactly_like_h3() -> None:
    """Frozen invariant: labeling never alters the trade population."""
    rows = annotate(synthetic_rows())

    def feed(sim_class: type[FastH3Simulator]) -> FastH3Simulator:
        s15 = FastStructure(2, 1.5, 0.0)
        sc = FastStructure(3, 1.5, 0.0)
        sim = sim_class(2.0, 3.0, s15, sc, log_trades=True)
        for tf_idx, warmup, ots, o, h, lo, c, prof in rows:
            if tf_idx == TF_15M:
                if isinstance(sim, FastH4Simulator):
                    sim.prof = prof
                sim.on_5m(warmup, ots, o, h, lo, c, s15.update(o, h, lo, c))
            else:
                sc.update(o, h, lo, c)
        sim.finalize()
        return sim

    h4 = feed(FastH4Simulator)
    h3 = feed(FastH3Simulator)
    assert h4.metrics == h3.metrics
    assert h4.trade_log == h3.trade_log


def test_h4_run_shard_deterministic() -> None:
    rows = annotate(synthetic_rows(960))
    configs = [
        (0, TF_4H, 2, 1, 2.0, 0.0, 2.0, 3.0),
        (1, TF_4H, 3, 0, 2.0, 0.1, 1.5, 4.0),
    ]
    a = run_shard_h4(rows, configs, log_trades=True)
    b = run_shard_h4(rows, configs, log_trades=True)

    def strip(res: list) -> list:
        return [(i, m, t, bs, pi, ll) for i, m, _c, t, bs, pi, ll in res]

    assert strip(a) == strip(b)

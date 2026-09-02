"""H4 equivalence harness (ADR-0003 + EXP-20260902-003 freeze): 90-day
trade-by-trade Decimal reference vs fast mirror on all 96 frozen
configurations, BOTH instruments (user order), with LABEL PARITY — the
(side, bucket) journal compared exactly per trade — plus per-(side,
bucket) counters, primary_ignored, hash determinism, and the frozen
invariant that H4's global metrics equal FastH3's on the same rows
(labels never alter the population). The synthetic mini-equivalence
lives in CI (tests/unit/test_h4fast.py). Exit 0 only when green.

Usage: python scripts/equivalence_h4.py
"""

from __future__ import annotations

import hashlib
import os
import sys
import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from quantlab.core.clock import SimulatedClock
from quantlab.core.config import AppConfig
from quantlab.core.logging import configure_logging
from quantlab.data.datasets import SeriesResolver
from quantlab.data.replay import replay_candles
from quantlab.domain.models import Timeframe
from quantlab.profile import VolumeProfileEngine
from quantlab.research.baseline import FillModel
from quantlab.research.fast.equivalence import compare_trade_logs, rel_equal
from quantlab.research.fast.extract import extract_rows_multi_h4
from quantlab.research.fast.h3fast import TF_4H, run_shard_h3
from quantlab.research.fast.h4fast import run_shard_h4
from quantlab.research.h1 import H1Config
from quantlab.research.h4 import H4LoggingSimulator
from quantlab.storage.postgres.adapter import (
    PostgresAuditEventWriter,
    PostgresCandleSnapshotFactory,
    PostgresDataQualityEventRepository,
    PostgresDatasetRepository,
    PostgresInstrumentRepository,
    PostgresVenueRepository,
)
from quantlab.structure.breaks import ValidationMethod
from quantlab.structure.engine import DetectorKind, MarketStructureEngine, StructureConfig
from run_h4_fast import DATASET, TIMEFRAMES, configs_list

WINDOW_90D = (datetime(2021, 1, 1, tzinfo=UTC), datetime(2021, 4, 1, tzinfo=UTC))


def engine_for(det_is_atr: int, n: int, mult: float, buf: float) -> MarketStructureEngine:
    return MarketStructureEngine(
        StructureConfig(
            detector=DetectorKind.ATR if det_is_atr else DetectorKind.FRACTAL,
            n=n,
            atr_multiplier=Decimal(str(mult)),
            validation=ValidationMethod.ATR_BUFFER if buf > 0 else ValidationMethod.CLOSE,
            breakout_buffer=Decimal(str(buf)),
        )
    )


def slow_results(url: str, symbol: str) -> dict[int, tuple[list, list, dict, int]]:
    """index -> (trade_log, label_log, bucket_stats, primary_ignored)."""
    start, end = WINDOW_90D
    datasets = PostgresDatasetRepository(url)
    resolve = SeriesResolver(PostgresVenueRepository(url), PostgresInstrumentRepository(url))
    configs = configs_list()
    engines_15m: dict[tuple, MarketStructureEngine] = {}
    engines_ctx: dict[tuple, MarketStructureEngine] = {}
    for _i, ctx, n15, det, mult, buf, _r, _k in configs:
        k15 = (n15, det, mult, buf)
        kc = (ctx, det, mult, buf)
        if k15 not in engines_15m:
            engines_15m[k15] = engine_for(det, n15, mult, buf)
        if kc not in engines_ctx:
            n_ctx = 5 if ctx == TF_4H else 3
            engines_ctx[kc] = engine_for(det, n_ctx, mult, buf)
    sims: dict[int, tuple[H4LoggingSimulator, tuple]] = {}
    keys: dict[Timeframe, object] = {}
    fill = FillModel()
    profiles = VolumeProfileEngine()

    for event in replay_candles(
        PostgresCandleSnapshotFactory(url),
        datasets,
        resolve,
        PostgresDataQualityEventRepository(url),
        PostgresAuditEventWriter(url),
        *DATASET,
        SimulatedClock(start),
        symbols=[symbol],
        timeframes=TIMEFRAMES,
        start=start,
        end=end,
        lookback=timedelta(days=30),
    ):
        tf = event.series.timeframe
        keys[tf] = event.series
        if tf is not Timeframe.M15:
            ctx_idx = 1 if tf is Timeframe.H4 else 2
            for kc, engine in engines_ctx.items():
                if kc[0] == ctx_idx:
                    engine.on_event(event)
            continue
        profiles.on_event(event)  # fed BEFORE the simulators, as everywhere
        if not sims:
            for i, ctx, n15, det, mult, buf, r, k in configs:
                key_ctx = keys.get(Timeframe.H4 if ctx == TF_4H else Timeframe.D1)
                if key_ctx is None:  # context key deterministic from the 15m key
                    key_ctx = type(event.series)(
                        venue=event.series.venue,
                        venue_symbol=event.series.venue_symbol,
                        timeframe=Timeframe.H4 if ctx == TF_4H else Timeframe.D1,
                        source=event.series.source,
                    )
                sims[i] = (
                    H4LoggingSimulator(
                        H1Config(
                            n15,
                            0,
                            Decimal(str(mult)),
                            Decimal(str(buf)),
                            Decimal(str(r)),
                            Decimal("0"),
                        ),
                        engines_15m[(n15, det, mult, buf)],
                        engines_ctx[(ctx, det, mult, buf)],
                        event.series,
                        key_ctx,
                        fill,
                        k_stop=Decimal(str(k)),
                        profiles=profiles,
                    ),
                    (n15, det, mult, buf),
                )
        outs = {k15: engine.on_event(event) for k15, engine in engines_15m.items()}
        for sim, k15 in sims.values():
            sim.on_5m(event, outs[k15])
    for sim, _k15 in sims.values():
        sim.finalize()
    return {
        i: (sim.trade_log, sim.label_log, sim.bucket_stats, sim.primary_ignored)
        for i, (sim, _k15) in sims.items()
    }


def check_symbol(url: str, symbol: str) -> int:
    start, end = WINDOW_90D
    print(f"H4 equivalence {symbol}: window [{start.date()} → {end.date()}), Decimal reference…")
    t0 = time.monotonic()
    slow = slow_results(url, symbol)
    print(f"  slow pass done in {(time.monotonic() - t0) / 60:.1f} min")

    print(f"H4 equivalence {symbol}: fast path, twice (determinism)…")
    rows = extract_rows_multi_h4(url, *DATASET, symbol, start, end, TIMEFRAMES)
    fast_a = run_shard_h4(rows, configs_list(), log_trades=True)
    fast_b = run_shard_h4(rows, configs_list(), log_trades=True)

    def digest(result: list) -> str:
        payload = repr([(i, m, t, bs, pi, ll) for i, m, _c, t, bs, pi, ll in result])
        return hashlib.sha256(payload.encode()).hexdigest()

    digest_a, digest_b = digest(fast_a), digest(fast_b)
    if digest_a != digest_b:
        print(f"DETERMINISM FAILED: {digest_a} != {digest_b}", file=sys.stderr)
        return 1
    print(f"  determinism OK: {digest_a[:16]}…")

    # frozen invariant: labels never alter the population — H4 == H3 globally
    h3 = run_shard_h3([r[:7] for r in rows], configs_list())
    h3_metrics = {i: m for i, m, _c, _t in h3}
    diffs: list[str] = []
    total = 0
    labels_total = 0
    primary_total = 0
    for index, metrics, _context, log, buckets, primary_ignored, label_log in fast_a:
        if metrics != h3_metrics[index]:
            diffs.append(f"cfg{index}: H4 global metrics differ from FastH3 (population drift)")
        slow_log, slow_labels, slow_buckets, slow_primary_ignored = slow[index]
        total += len(slow_log)
        labels_total += len(slow_labels)
        diffs.extend(compare_trade_logs(slow_log, log or [], f"cfg{index}"))
        if slow_labels != label_log:
            first = next(
                (j for j, (a, b) in enumerate(zip(slow_labels, label_log, strict=False)) if a != b),
                min(len(slow_labels), len(label_log)),
            )
            diffs.append(
                f"cfg{index}: LABELS differ at trade {first} "
                f"(slow {slow_labels[first : first + 2]} vs fast {label_log[first : first + 2]})"
            )
        if slow_primary_ignored != primary_ignored:
            diffs.append(
                f"cfg{index}: primary_ignored {slow_primary_ignored} (slow) "
                f"!= {primary_ignored} (fast)"
            )
        for key, s_stats in slow_buckets.items():
            f_stats = buckets[key]
            if (s_stats.trades, s_stats.wins, s_stats.dominated) != (
                f_stats.trades,
                f_stats.wins,
                f_stats.dominated,
            ):
                diffs.append(f"cfg{index} bucket {key}: counters differ")
            elif not (
                rel_equal(float(s_stats.sum_r), f_stats.sum_r)
                and rel_equal(float(s_stats.pos_r), f_stats.pos_r)
                and rel_equal(float(s_stats.neg_r), f_stats.neg_r)
                and rel_equal(float(s_stats.sum_cost_r), f_stats.sum_cost_r)
            ):
                diffs.append(f"cfg{index} bucket {key}: sums beyond rel 1e-9")
        primary_total += buckets[(1, 3)].trades + buckets[(-1, 4)].trades
    if diffs:
        print(
            f"H4 EQUIVALENCE FAILED ({symbol}): {len(diffs)} difference(s); first 10:",
            file=sys.stderr,
        )
        for d in diffs[:10]:
            print(f"  {d}", file=sys.stderr)
        return 1
    print(
        f"  H4 equivalence OK ({symbol}): {total} trades across 96 configurations, "
        f"labels exact ({labels_total} labelled, {primary_total} primary), "
        "H3-population invariant holds, timings/side exact, prices and R within rel 1e-9"
    )
    return 0


def main() -> int:
    url = os.environ.get("QUANTLAB_DATABASE_URL")
    if not url:
        print("QUANTLAB_DATABASE_URL is not set", file=sys.stderr)
        return 2
    configure_logging(AppConfig.load().log_level)
    for symbol in ("BTCUSDT", "ETHUSDT"):
        code = check_symbol(url, symbol)
        if code != 0:
            return code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

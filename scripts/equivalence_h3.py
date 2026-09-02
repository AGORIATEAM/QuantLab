"""H3 equivalence harness (ADR-0003): 90-day trade-by-trade Decimal
reference vs fast mirror on all 96 frozen configurations, plus hash
determinism of the fast path and an exact per-config comparison of the
new stop_atr_dominated counter. The synthetic mini-equivalence lives in
CI (tests/unit/test_h3fast.py). Exit 0 only when green.

Usage: python scripts/equivalence_h3.py [SYMBOL]
    SYMBOL defaults to BTCUSDT; ETHUSDT runs the ADR-0003 ETH complement.
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
from quantlab.research.baseline import FillModel
from quantlab.research.fast.equivalence import compare_trade_logs
from quantlab.research.fast.extract import extract_rows_multi
from quantlab.research.fast.h3fast import TF_4H, run_shard_h3
from quantlab.research.h1 import H1Config
from quantlab.research.h3 import H3LoggingSimulator
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
from run_h3_fast import DATASET, TIMEFRAMES, configs_list

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


def slow_results(url: str, symbol: str) -> dict[int, tuple[list, int]]:
    """index -> (trade_log, stop_atr_dominated) from the Decimal reference."""
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
    sims: dict[int, tuple[H3LoggingSimulator, tuple]] = {}
    keys: dict[Timeframe, object] = {}
    fill = FillModel()

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
                    H3LoggingSimulator(
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
                    ),
                    (n15, det, mult, buf),
                )
        outs = {k15: engine.on_event(event) for k15, engine in engines_15m.items()}
        for sim, k15 in sims.values():
            sim.on_5m(event, outs[k15])
    for sim, _k15 in sims.values():
        sim.finalize()
    return {i: (sim.trade_log, sim.metrics.stop_atr_dominated) for i, (sim, _k15) in sims.items()}


def main(argv: list[str]) -> int:
    symbol = argv[0] if argv else "BTCUSDT"
    url = os.environ.get("QUANTLAB_DATABASE_URL")
    if not url:
        print("QUANTLAB_DATABASE_URL is not set", file=sys.stderr)
        return 2
    configure_logging(AppConfig.load().log_level)
    start, end = WINDOW_90D

    print(f"H3 equivalence {symbol}: window [{start.date()} → {end.date()}), Decimal reference…")
    t0 = time.monotonic()
    slow = slow_results(url, symbol)
    print(f"  slow pass done in {(time.monotonic() - t0) / 60:.1f} min")

    print("H3 equivalence: fast path, twice (determinism)…")
    rows = extract_rows_multi(url, *DATASET, symbol, start, end, TIMEFRAMES)
    fast_a = run_shard_h3(rows, configs_list(), log_trades=True)
    fast_b = run_shard_h3(rows, configs_list(), log_trades=True)
    digest_a = hashlib.sha256(repr([(i, m, t) for i, m, _c, t in fast_a]).encode()).hexdigest()
    digest_b = hashlib.sha256(repr([(i, m, t) for i, m, _c, t in fast_b]).encode()).hexdigest()
    if digest_a != digest_b:
        print(f"DETERMINISM FAILED: {digest_a} != {digest_b}", file=sys.stderr)
        return 1
    print(f"  determinism OK: {digest_a[:16]}…")

    total = 0
    dominated_total = 0
    diffs: list[str] = []
    for index, metrics, _context, log in fast_a:
        slow_log, slow_dominated = slow[index]
        total += len(slow_log)
        dominated_total += slow_dominated
        diffs.extend(compare_trade_logs(slow_log, log or [], f"cfg{index}"))
        if metrics.stop_atr_dominated != slow_dominated:
            diffs.append(
                f"cfg{index}: stop_atr_dominated {slow_dominated} (slow) "
                f"!= {metrics.stop_atr_dominated} (fast)"
            )
    if diffs:
        print(f"H3 EQUIVALENCE FAILED: {len(diffs)} difference(s); first 10:", file=sys.stderr)
        for d in diffs[:10]:
            print(f"  {d}", file=sys.stderr)
        return 1
    print(
        f"  H3 equivalence OK ({symbol}): {total} trades across 96 configurations "
        f"({dominated_total} ATR-dominated stops, counters exact), "
        "timings/side exact, prices and R within rel 1e-9"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

"""ADR-0003 equivalence harness against the golden BTC in-sample CSV.

Usage:
    python scripts/equivalence_h1.py --level 1   # aggregate vs golden + determinism
    python scripts/equivalence_h1.py --level 2   # 90-day trade-by-trade vs Decimal ref

Level 1: full BTC in-sample on the fast path, twice — 216 rows compared to
the golden CSV (integer counters exact, monetary/R at rel 1e-9) and the
two fast runs compared by SHA-256 (determinism).
Level 2: [2021-01-01, 2021-04-01), lookback 30d: the untouched Decimal
reference (LoggingSimulator subclass) versus the fast path, trade by
trade, all 216 configurations. Exit code 0 only when green.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import sys
import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from itertools import product

from quantlab.core.clock import SimulatedClock
from quantlab.core.config import AppConfig
from quantlab.core.logging import configure_logging
from quantlab.data.datasets import SeriesResolver
from quantlab.data.replay import replay_candles
from quantlab.domain.models import Timeframe
from quantlab.research.baseline import FillModel
from quantlab.research.fast.equivalence import (
    LoggingSimulator,
    compare_metric_rows,
    compare_trade_logs,
)
from quantlab.research.fast.extract import extract_rows
from quantlab.research.fast.h1fast import run_shard
from quantlab.research.h1 import H1Config
from quantlab.storage.postgres.adapter import (
    PostgresAuditEventWriter,
    PostgresCandleSnapshotFactory,
    PostgresDataQualityEventRepository,
    PostgresDatasetRepository,
    PostgresInstrumentRepository,
    PostgresVenueRepository,
)
from quantlab.structure.engine import MarketStructureEngine
from run_h1 import BUFFERS, DATASET, MIN_STOPS, MULTS, N_1H, N_5M, R_TARGETS
from run_h1_fast import EXP_DIR, configs_list, run_symbol_fast

GOLDEN = EXP_DIR / "insample_BTCUSDT_metrics.csv"
GOLDEN_SHA256 = "3de5d0b427ec2f403e29457bd6445d1c496c42a82b26a0ec6480f66af2ff12b5"
WINDOW_90D = (datetime(2021, 1, 1, tzinfo=UTC), datetime(2021, 4, 1, tzinfo=UTC))


def level_1(url: str, workers: int) -> int:
    digest = hashlib.sha256(GOLDEN.read_bytes()).hexdigest()
    if digest != GOLDEN_SHA256:
        print(f"FATAL: golden CSV fingerprint changed ({digest})", file=sys.stderr)
        return 1
    reference = list(csv.DictReader(GOLDEN.open()))

    print("level 1: fast BTC in-sample, run A…")
    rows_a, extract_s, compute_s = run_symbol_fast(url, "BTCUSDT", "insample", workers)
    print(f"  run A: extract {extract_s:.0f}s, compute {compute_s:.0f}s")
    print("level 1: fast BTC in-sample, run B (determinism)…")
    rows_b, _, _ = run_symbol_fast(url, "BTCUSDT", "insample", workers)

    def digest_rows(rows: list[dict[str, object]]) -> str:
        payload = repr([sorted(r.items()) for r in rows]).encode()
        return hashlib.sha256(payload).hexdigest()

    da, db = digest_rows(rows_a), digest_rows(rows_b)
    if da != db:
        print(f"DETERMINISM FAILED: {da} != {db}", file=sys.stderr)
        return 1
    print(f"  determinism OK: both runs hash {da[:16]}…")

    diffs = compare_metric_rows(reference, rows_a, "L1")
    if diffs:
        print(f"LEVEL 1 FAILED: {len(diffs)} difference(s); first 10:", file=sys.stderr)
        for d in diffs[:10]:
            print(f"  {d}", file=sys.stderr)
        return 1
    print("  level 1 OK: 216 configurations reproduce the golden CSV (exact counters, rel 1e-9)")
    return 0


def slow_trade_logs_90d(url: str) -> dict[tuple, list]:
    """The untouched Decimal reference over the 90-day window, all configs,
    with the LoggingSimulator subclass journaling trades."""
    start, end = WINDOW_90D
    datasets = PostgresDatasetRepository(url)
    resolve = SeriesResolver(PostgresVenueRepository(url), PostgresInstrumentRepository(url))
    engines_5m: dict[tuple, MarketStructureEngine] = {}
    engines_1h: dict[tuple, MarketStructureEngine] = {}
    for n, mult, buf in product(N_5M, MULTS, BUFFERS):
        engines_5m[(n, mult, buf)] = MarketStructureEngine(
            H1Config(n, 0, mult, buf, Decimal(1), Decimal(0)).engine_config(n)
        )
    for n, mult, buf in product(N_1H, MULTS, BUFFERS):
        engines_1h[(n, mult, buf)] = MarketStructureEngine(
            H1Config(0, n, mult, buf, Decimal(1), Decimal(0)).engine_config(n)
        )
    sims: dict[tuple, LoggingSimulator] = {}
    key_5m = key_1h = None
    fill = FillModel()
    for event in replay_candles(
        PostgresCandleSnapshotFactory(url),
        datasets,
        resolve,
        PostgresDataQualityEventRepository(url),
        PostgresAuditEventWriter(url),
        *DATASET,
        SimulatedClock(start),
        symbols=["BTCUSDT"],
        timeframes=[Timeframe.M5, Timeframe.H1],
        start=start,
        end=end,
        lookback=timedelta(days=30),
    ):
        if event.series.timeframe is Timeframe.H1:
            key_1h = event.series
            for engine in engines_1h.values():
                engine.on_event(event)
            continue
        if key_5m is None:
            key_5m = event.series
            assert key_1h is not None
            for n5, n1, mult, buf, r, ms in product(
                N_5M, N_1H, MULTS, BUFFERS, R_TARGETS, MIN_STOPS
            ):
                config = H1Config(n5, n1, mult, buf, r, ms)
                sims[(n5, n1, float(mult), float(buf), float(r), float(ms))] = LoggingSimulator(
                    config,
                    engines_5m[(n5, mult, buf)],
                    engines_1h[(n1, mult, buf)],
                    key_5m,
                    key_1h,
                    fill,
                )
        outs = {key: engine.on_event(event) for key, engine in engines_5m.items()}
        for (n5, _n1, mult, buf, _r, _ms), sim in sims.items():
            sim.on_5m(event, outs[(n5, Decimal(str(mult)), Decimal(str(buf)))])
    for sim in sims.values():
        sim.finalize()
    return {key: sim.trade_log for key, sim in sims.items()}


def level_2(url: str) -> int:
    start, end = WINDOW_90D
    print(f"level 2: window [{start.date()} → {end.date()}), Decimal reference (slow)…")
    t0 = time.monotonic()
    slow_logs = slow_trade_logs_90d(url)
    print(f"  slow pass done in {(time.monotonic() - t0) / 60:.1f} min")

    print("level 2: fast path over the same window…")
    rows = extract_rows(url, *DATASET, "BTCUSDT", start, end)
    fast_results = run_shard(rows, configs_list(), log_trades=True)
    configs = configs_list()

    total_trades = 0
    all_diffs: list[str] = []
    for index, _metrics, _context, log in fast_results:
        _, n5, n1, mult, buf, r, ms = configs[index]
        slow_log = slow_logs[(n5, n1, mult, buf, r, ms)]
        total_trades += len(slow_log)
        all_diffs.extend(compare_trade_logs(slow_log, log or [], f"cfg{index}"))
    if all_diffs:
        print(f"LEVEL 2 FAILED: {len(all_diffs)} difference(s); first 10:", file=sys.stderr)
        for d in all_diffs[:10]:
            print(f"  {d}", file=sys.stderr)
        return 1
    print(
        f"  level 2 OK: {total_trades} trades compared across 216 configurations, "
        "timings/side exact, prices and R within rel 1e-9"
    )
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--level", required=True, choices=["1", "2"])
    parser.add_argument("--workers", type=int, default=os.cpu_count() or 4)
    args = parser.parse_args(argv)
    url = os.environ.get("QUANTLAB_DATABASE_URL")
    if not url:
        print("QUANTLAB_DATABASE_URL is not set", file=sys.stderr)
        return 2
    configure_logging(AppConfig.load().log_level)
    return level_1(url, args.workers) if args.level == "1" else level_2(url)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

"""EXP-20260902-001 (H2) on the ADR-0003 fast path — 288 frozen configs.

Usage:
    python scripts/run_h2_fast.py --period insample [--symbols ...]
    python scripts/run_h2_fast.py --period oos     # ONLY on explicit user go

Writes <period>_<symbol>_metrics.csv in the experiment directory, ordered
by configuration index, SHA-256 printed (determinism evidence).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from decimal import Decimal
from itertools import product
from pathlib import Path
from statistics import median

from quantlab.core.config import AppConfig
from quantlab.core.logging import configure_logging
from quantlab.domain.models import Timeframe
from quantlab.research.fast.extract import extract_rows_multi
from quantlab.research.fast.h1fast import FastContext, FastMetrics
from quantlab.research.fast.h2fast import (
    TF_1H,
    TF_4H,
    H2Config,
    pool_init_h2,
    run_shard_h2_pooled,
)
from run_h1 import WINDOWS
from run_h1_fast import q4

DATASET = ("btc-eth-spot-binance", "v1")
EXP_DIR = (
    Path(__file__).resolve().parent.parent / "experiments" / "EXP-20260902-001-h2-failed-sweep"
)
TIMEFRAMES = [Timeframe.M5, Timeframe.H1, Timeframe.H4]  # MultiRow index order
CONTEXT_LABEL = {TF_1H: "1h_n8", TF_4H: "4h_n5"}
# frozen neighborhoods (experiment.json, 2026-09-02): 288 configurations
CONTEXTS = [TF_1H, TF_4H]
N_5M = [2, 3]
DETECTORS: list[tuple[int, float]] = [(0, 2.0), (1, 1.5), (1, 2.0), (1, 3.0)]  # (is_atr, mult)
BUFFERS = [0.0, 0.1]
MIN_STOPS = [0.0, 0.3, 0.5]
R_TARGETS = [1.5, 2.0, 3.0]

FIELDS = [
    "context",
    "n_5m",
    "detector",
    "atr_mult",
    "buffer",
    "r_target",
    "min_stop_atr",
    "trades",
    "expectancy_r",
    "profit_factor",
    "win_rate_pct",
    "max_drawdown_pct",
    "net_return_pct",
    "fees_paid",
    "exposure_pct",
    "sharpe_annualized",
    "avg_cost_r",
    "avg_stop_pct",
    "trades_per_day",
    "capped_share_pct",
    "skipped_min_stop",
    "ignored_in_position",
    "pct_time_neutral_context",
    "context_state_changes_per_week",
]


def configs_list() -> list[H2Config]:
    grid = product(CONTEXTS, N_5M, DETECTORS, BUFFERS, R_TARGETS, MIN_STOPS)
    return [
        (i, ctx, n5, det, mult, buf, r, ms)
        for i, (ctx, n5, (det, mult), buf, r, ms) in enumerate(grid)
    ]


def h2_row(config: H2Config, m: FastMetrics, context: FastContext, days: int) -> dict[str, object]:
    _, ctx, n5, det, mult, buf, r, ms = config

    def dec(value: float) -> str:
        return str(Decimal(repr(value)).normalize()) if value == int(value) else str(value)

    trades = m.trades
    return {
        "context": CONTEXT_LABEL[ctx],
        "n_5m": n5,
        "detector": "atr" if det else "fractal",
        "atr_mult": dec(mult) if det else "-",
        "buffer": dec(buf),
        "r_target": dec(r),
        "min_stop_atr": dec(ms),
        "trades": trades,
        "expectancy_r": q4(m.sum_r / trades) if trades else "",
        "profit_factor": q4(m.gross_profit / m.gross_loss) if m.gross_loss > 0 else "",
        "win_rate_pct": q4(m.wins / trades * 100) if trades else "",
        "max_drawdown_pct": q4(m.max_drawdown_pct),
        "net_return_pct": q4((m.final_equity / 10_000.0 - 1) * 100),
        "fees_paid": q4(m.fees_paid),
        "exposure_pct": q4(m.bars_in_position / m.bars * 100) if m.bars else "",
        "sharpe_annualized": round(m.sharpe_annualized, 3) if m.sharpe_annualized else "",
        "avg_cost_r": q4(m.sum_cost_r / trades) if trades else "",
        "avg_stop_pct": q4(m.sum_stop_pct / trades) if trades else "",
        "trades_per_day": q4(trades / days),
        "capped_share_pct": q4(m.capped / trades * 100) if trades else "",
        "skipped_min_stop": m.skipped_min_stop,
        "ignored_in_position": m.ignored_in_position,
        "pct_time_neutral_context": q4(context.neutral / context.bars * 100)
        if context.bars
        else "",
        "context_state_changes_per_week": q4(context.changes / days * 7) if days else "",
    }


def run_symbol(url: str, symbol: str, period: str, workers: int) -> tuple[list[dict], float, float]:
    start, end = WINDOWS[period]
    days = (end - start).days
    t0 = time.monotonic()
    rows = extract_rows_multi(url, *DATASET, symbol, start, end, TIMEFRAMES)
    extract_s = time.monotonic() - t0
    configs = configs_list()
    shards = [configs[i::workers] for i in range(workers)]
    t1 = time.monotonic()
    results: dict[int, tuple[FastMetrics, FastContext]] = {}
    with ProcessPoolExecutor(
        max_workers=workers, initializer=pool_init_h2, initargs=(rows,)
    ) as pool:
        for shard_result in pool.map(run_shard_h2_pooled, shards):
            for index, metrics, context, _log in shard_result:
                results[index] = (metrics, context)
    compute_s = time.monotonic() - t1
    out = [h2_row(configs[i], *results[i], days) for i in range(len(configs))]
    return out, extract_s, compute_s


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--period", required=True, choices=["insample", "oos"])
    parser.add_argument("--symbols", default="BTCUSDT,ETHUSDT")
    parser.add_argument("--workers", type=int, default=os.cpu_count() or 4)
    args = parser.parse_args(argv)
    url = os.environ.get("QUANTLAB_DATABASE_URL")
    if not url:
        print("QUANTLAB_DATABASE_URL is not set", file=sys.stderr)
        return 2
    configure_logging(AppConfig.load().log_level)

    print(f"== EXP-20260902-001 {args.period} (fast, {args.workers} workers, 288 configs) ==")
    total0 = time.monotonic()
    for symbol in args.symbols.split(","):
        symbol = symbol.strip()
        rows, extract_s, compute_s = run_symbol(url, symbol, args.period, args.workers)
        out = EXP_DIR / f"{args.period}_{symbol}_metrics.csv"
        with out.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        digest = hashlib.sha256(out.read_bytes()).hexdigest()
        expectancies = [float(r["expectancy_r"]) for r in rows if r["expectancy_r"] != ""]
        positives = sum(1 for e in expectancies if e > 0)
        print(
            f"  {symbol}: extract {extract_s:.0f}s, compute {compute_s:.0f}s -> {out.name}\n"
            f"    sha256 {digest}\n"
            f"    expectancy_r median {median(expectancies):+.4f} "
            f"[{min(expectancies):+.4f}, {max(expectancies):+.4f}], "
            f">0: {positives}/{len(expectancies)}"
        )
    print(f"total: {(time.monotonic() - total0) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

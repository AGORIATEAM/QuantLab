"""EXP-20260902-003 (H4) on the ADR-0003 fast path — 96 frozen configs.

Usage:
    python scripts/run_h4_fast.py --period insample [--symbols ...]
    python scripts/run_h4_fast.py --period oos     # ONLY on explicit user go

Writes <period>_<symbol>_metrics.csv in the experiment directory:
the H3 global columns (identical trade population), six per-bucket
blocks (directions pooled), the PRIMARY subset block (long x sous_val
UNION short x sur_vah, PF in R), the evaluable flag (>= 100 primary IS
trades, frozen guardrail) and the primary swallowing share (frozen
addition). SHA-256 printed (determinism evidence).
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
from quantlab.profile import BUCKETS
from quantlab.research.fast.extract import extract_rows_multi_h4
from quantlab.research.fast.h1fast import FastContext, FastMetrics
from quantlab.research.fast.h3fast import TF_1D, TF_4H, H3Config
from quantlab.research.fast.h4fast import (
    SOUS_VAL,
    SUR_VAH,
    FastBucketStats,
    pool_init_h4,
    run_shard_h4_pooled,
)
from run_h1 import WINDOWS
from run_h1_fast import q4

DATASET = ("btc-eth-spot-binance", "v1")
EXP_DIR = (
    Path(__file__).resolve().parent.parent
    / "experiments"
    / "EXP-20260902-003-h4-value-located-sweep"
)
TIMEFRAMES = [Timeframe.M15, Timeframe.H4, Timeframe.D1]  # MultiRow index order
CONTEXT_LABEL = {TF_4H: "4h_n5", TF_1D: "1d_n3"}
# frozen neighborhoods (EXP-20260902-002, inherited): 96 configurations
CONTEXTS = [TF_4H, TF_1D]
N_15M = [2, 3]
DETECTORS: list[tuple[int, float]] = [(0, 2.0), (1, 2.0)]  # (is_atr, mult)
BUFFERS = [0.0, 0.1]
K_STOPS = [3.0, 4.0]
R_TARGETS = [1.5, 2.0, 3.0]
MIN_PRIMARY_TRADES = 100  # frozen sample guardrail

GLOBAL_FIELDS = [
    "context",
    "n_15m",
    "detector",
    "atr_mult",
    "buffer",
    "r_target",
    "k_stop",
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
    "share_stop_dominated_pct",
    "ignored_in_position",
    "pct_time_neutral_context",
    "context_state_changes_per_week",
]
BUCKET_METRICS = [
    "trades",
    "share_pct",
    "exp_r",
    "gross_r",
    "pf_r",
    "win_pct",
    "cost_r",
    "stop_pct",
    "dom_pct",
]
PRIMARY_FIELDS = [
    "primary_trades",
    "primary_exp_r",
    "primary_gross_r",
    "primary_pf_r",
    "primary_win_pct",
    "evaluable",
    "primary_ignored",
    "primary_swallowed_share_pct",
]
FIELDS = (
    GLOBAL_FIELDS
    + [f"{bucket}_{metric}" for bucket in BUCKETS for metric in BUCKET_METRICS]
    + PRIMARY_FIELDS
)


def configs_list() -> list[H3Config]:
    grid = product(CONTEXTS, N_15M, DETECTORS, BUFFERS, R_TARGETS, K_STOPS)
    return [
        (i, ctx, n15, det, mult, buf, r, k)
        for i, (ctx, n15, (det, mult), buf, r, k) in enumerate(grid)
    ]


def _merge(cells: list[FastBucketStats]) -> FastBucketStats:
    out = FastBucketStats()
    for cell in cells:
        out.trades += cell.trades
        out.wins += cell.wins
        out.sum_r += cell.sum_r
        out.pos_r += cell.pos_r
        out.neg_r += cell.neg_r
        out.sum_cost_r += cell.sum_cost_r
        out.sum_stop_pct += cell.sum_stop_pct
        out.dominated += cell.dominated
    return out


def _stats_block(stats: FastBucketStats, total_trades: int) -> dict[str, object]:
    t = stats.trades
    return {
        "trades": t,
        "share_pct": q4(t / total_trades * 100) if total_trades else "",
        "exp_r": q4(stats.sum_r / t) if t else "",
        "gross_r": q4((stats.sum_r + stats.sum_cost_r) / t) if t else "",
        "pf_r": q4(stats.pos_r / stats.neg_r) if stats.neg_r > 0 else "",
        "win_pct": q4(stats.wins / t * 100) if t else "",
        "cost_r": q4(stats.sum_cost_r / t) if t else "",
        "stop_pct": q4(stats.sum_stop_pct / t) if t else "",
        "dom_pct": q4(stats.dominated / t * 100) if t else "",
    }


def h4_row(
    config: H3Config,
    m: FastMetrics,
    context: FastContext,
    buckets: dict[tuple[int, int], FastBucketStats],
    primary_ignored: int,
    days: int,
) -> dict[str, object]:
    _, ctx, n15, det, mult, buf, r, k = config

    def dec(value: float) -> str:
        return str(Decimal(repr(value)).normalize()) if value == int(value) else str(value)

    trades = m.trades
    row: dict[str, object] = {
        "context": CONTEXT_LABEL[ctx],
        "n_15m": n15,
        "detector": "atr" if det else "fractal",
        "atr_mult": dec(mult) if det else "-",
        "buffer": dec(buf),
        "r_target": dec(r),
        "k_stop": dec(k),
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
        "share_stop_dominated_pct": q4(m.stop_atr_dominated / trades * 100) if trades else "",
        "ignored_in_position": m.ignored_in_position,
        "pct_time_neutral_context": q4(context.neutral / context.bars * 100)
        if context.bars
        else "",
        "context_state_changes_per_week": q4(context.changes / days * 7) if days else "",
    }
    for bucket_idx, bucket_name in enumerate(BUCKETS):
        merged = _merge([buckets[(1, bucket_idx)], buckets[(-1, bucket_idx)]])
        for metric, value in _stats_block(merged, trades).items():
            row[f"{bucket_name}_{metric}"] = value
    primary = _merge([buckets[(1, SOUS_VAL)], buckets[(-1, SUR_VAH)]])
    block = _stats_block(primary, trades)
    row["primary_trades"] = primary.trades
    row["primary_exp_r"] = block["exp_r"]
    row["primary_gross_r"] = block["gross_r"]
    row["primary_pf_r"] = block["pf_r"]
    row["primary_win_pct"] = block["win_pct"]
    row["evaluable"] = int(primary.trades >= MIN_PRIMARY_TRADES)
    row["primary_ignored"] = primary_ignored
    swallowed_base = primary_ignored + primary.trades
    row["primary_swallowed_share_pct"] = (
        q4(primary_ignored / swallowed_base * 100) if swallowed_base else ""
    )
    return row


def run_symbol(url: str, symbol: str, period: str, workers: int) -> tuple[list[dict], float, float]:
    start, end = WINDOWS[period]
    days = (end - start).days
    t0 = time.monotonic()
    rows = extract_rows_multi_h4(url, *DATASET, symbol, start, end, TIMEFRAMES)
    extract_s = time.monotonic() - t0
    configs = configs_list()
    shards = [configs[i::workers] for i in range(workers)]
    t1 = time.monotonic()
    results: dict[int, tuple] = {}
    with ProcessPoolExecutor(
        max_workers=workers, initializer=pool_init_h4, initargs=(rows,)
    ) as pool:
        for shard_result in pool.map(run_shard_h4_pooled, shards):
            for index, metrics, context, _log, buckets, primary_ignored, _labels in shard_result:
                results[index] = (metrics, context, buckets, primary_ignored)
    compute_s = time.monotonic() - t1
    out = [h4_row(configs[i], *results[i], days) for i in range(len(configs))]
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

    print(f"== EXP-20260902-003 {args.period} (fast, {args.workers} workers, 96 configs) ==")
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
        evaluable = [r for r in rows if r["evaluable"] == 1]
        primary_exp = [float(r["primary_exp_r"]) for r in evaluable if r["primary_exp_r"] != ""]
        positives = sum(1 for e in primary_exp if e > 0)
        summary = (
            f"    primary expectancy_r median {median(primary_exp):+.4f} "
            f"[{min(primary_exp):+.4f}, {max(primary_exp):+.4f}], "
            f">0: {positives}/{len(primary_exp)}"
            if primary_exp
            else "    NO evaluable configuration (all < 100 primary trades)"
        )
        print(
            f"  {symbol}: extract {extract_s:.0f}s, compute {compute_s:.0f}s -> {out.name}\n"
            f"    sha256 {digest}\n"
            f"    evaluable {len(evaluable)}/96 (guardrail {MIN_PRIMARY_TRADES} primary trades)\n"
            + summary
        )
    print(f"total: {(time.monotonic() - total0) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

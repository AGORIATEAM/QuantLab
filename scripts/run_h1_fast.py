"""EXP-20260901-003 on the ADR-0003 fast path (float64 hot loop,
parallel shards over one extracted replay pass).

Usage:
    python scripts/run_h1_fast.py --period insample [--symbols ...]
    python scripts/run_h1_fast.py --period oos

Writes the same per-config CSV as scripts/run_h1.py (fast_ prefix free —
same filenames, this IS the runner now) plus the SHA-256 of each CSV for
the determinism check. Ordered by configuration index, independent of
worker completion order (ADR-0003 décision 4).
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
from quantlab.research.fast.extract import extract_rows
from quantlab.research.fast.h1fast import (
    FastContext,
    FastMetrics,
    pool_init,
    run_shard_pooled,
)
from run_h1 import (
    BUFFERS,
    DATASET,
    FIELDS,
    MIN_STOPS,
    MULTS,
    N_1H,
    N_5M,
    R_TARGETS,
    WINDOWS,
)

EXP_DIR = (
    Path(__file__).resolve().parent.parent
    / "experiments"
    / "EXP-20260901-003-h1-structure-alignment"
)


def configs_list() -> list[tuple[int, int, int, float, float, float, float]]:
    grid = product(N_5M, N_1H, MULTS, BUFFERS, R_TARGETS, MIN_STOPS)
    return [
        (i, n5, n1, float(mult), float(buf), float(r), float(ms))
        for i, (n5, n1, mult, buf, r, ms) in enumerate(grid)
    ]


def q4(value: float) -> str:
    # ADR-0003: float -> Decimal with explicit quantization at the boundary
    return str(Decimal(repr(value)).quantize(Decimal("0.0001")))


def fast_row(
    config: tuple[int, int, int, float, float, float, float],
    m: FastMetrics,
    context: FastContext,
    days: int,
) -> dict[str, object]:
    _, n5, n1, mult, buf, r, ms = config
    trades = m.trades

    def dec(value: float) -> str:
        return str(Decimal(repr(value)).normalize()) if value == int(value) else str(value)

    return {
        "n_5m": n5,
        "n_1h": n1,
        "atr_mult": dec(mult),
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
        "pct_time_neutral_1h": q4(context.neutral / context.bars * 100) if context.bars else "",
        "h1_state_changes_per_week": q4(context.changes / days * 7) if days else "",
    }


def run_symbol_fast(
    url: str, symbol: str, period: str, workers: int
) -> tuple[list[dict[str, object]], float, float]:
    start, end = WINDOWS[period]
    days = (end - start).days
    t0 = time.monotonic()
    rows = extract_rows(url, *DATASET, symbol, start, end)
    extract_s = time.monotonic() - t0

    configs = configs_list()
    shards = [configs[i::workers] for i in range(workers)]
    t1 = time.monotonic()
    results: dict[int, tuple[FastMetrics, FastContext]] = {}
    with ProcessPoolExecutor(max_workers=workers, initializer=pool_init, initargs=(rows,)) as pool:
        for shard_result in pool.map(run_shard_pooled, shards):
            for index, metrics, context, _log in shard_result:
                results[index] = (metrics, context)
    compute_s = time.monotonic() - t1
    out = [fast_row(configs[i], *results[i], days) for i in range(len(configs))]
    return out, extract_s, compute_s


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--period", required=True, choices=["insample", "oos"])
    parser.add_argument("--symbols", default="BTCUSDT,ETHUSDT")
    parser.add_argument("--workers", type=int, default=os.cpu_count() or 4)
    parser.add_argument("--suffix", default="", help="output filename suffix (equivalence runs)")
    args = parser.parse_args(argv)
    url = os.environ.get("QUANTLAB_DATABASE_URL")
    if not url:
        print("QUANTLAB_DATABASE_URL is not set", file=sys.stderr)
        return 2
    configure_logging(AppConfig.load().log_level)

    print(f"== EXP-20260901-003 {args.period} (fast, {args.workers} workers) ==")
    total0 = time.monotonic()
    for symbol in args.symbols.split(","):
        symbol = symbol.strip()
        rows, extract_s, compute_s = run_symbol_fast(url, symbol, args.period, args.workers)
        out = EXP_DIR / f"{args.period}_{symbol}_metrics{args.suffix}.csv"
        with out.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        digest = hashlib.sha256(out.read_bytes()).hexdigest()
        expectancies = [float(r["expectancy_r"]) for r in rows if r["expectancy_r"] != ""]
        print(
            f"  {symbol}: extract {extract_s:.0f}s, compute {compute_s:.0f}s, "
            f"{len(rows)} configs -> {out.name}\n"
            f"    sha256 {digest}\n"
            f"    expectancy_r median {median(expectancies):+.4f} "
            f"[{min(expectancies):+.4f}, {max(expectancies):+.4f}], "
            f">0: {sum(1 for e in expectancies if e > 0)}/{len(expectancies)}"
        )
    print(f"total: {(time.monotonic() - total0) / 60:.1f} min (budget ADR-0003: < 30 min)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

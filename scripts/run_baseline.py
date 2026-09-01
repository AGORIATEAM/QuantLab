"""Run a baseline experiment on the official dataset and record it
docs/21-style under experiments/ (T7bis).

Usage:
    python scripts/run_baseline.py --experiment buy-and-hold
    python scripts/run_baseline.py --experiment breakout [--n 24]

Records experiments/EXP-YYYYMMDD-NNN-<slug>/{experiment.json,equity.csv}.
Baselines only: the metrics carry no conclusion (docs/21 §22).
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

from quantlab.core.clock import SimulatedClock
from quantlab.core.config import AppConfig
from quantlab.core.logging import configure_logging
from quantlab.core.timeutils import utc_now
from quantlab.data.datasets import SeriesResolver
from quantlab.data.replay import replay_candles
from quantlab.domain.models import Timeframe
from quantlab.research.baseline import Breakout, BuyAndHold, FillModel, run_experiment
from quantlab.storage.postgres.adapter import (
    PostgresAuditEventWriter,
    PostgresCandleSnapshotFactory,
    PostgresDataQualityEventRepository,
    PostgresDatasetRepository,
    PostgresInstrumentRepository,
    PostgresVenueRepository,
)

DATASET_NAME = "btc-eth-spot-binance"
DATASET_VERSION = "v1"
SYMBOL = "BTCUSDT"
TIMEFRAME = Timeframe.H1
EXPERIMENTS_DIR = Path(__file__).resolve().parent.parent / "experiments"


def code_commit() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10
        )
        return out.stdout.strip() or None if out.returncode == 0 else None
    except OSError:
        return None


def next_experiment_id(when: str) -> str:
    existing = sorted(EXPERIMENTS_DIR.glob(f"EXP-{when}-*"))
    return f"EXP-{when}-{len(existing) + 1:03d}"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", required=True, choices=["buy-and-hold", "breakout"])
    parser.add_argument("--n", type=int, default=24, help="breakout window (candles)")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    url = os.environ.get("QUANTLAB_DATABASE_URL")
    if not url:
        print("QUANTLAB_DATABASE_URL is not set", file=sys.stderr)
        return 2
    configure_logging(AppConfig.load().log_level)

    datasets = PostgresDatasetRepository(url)
    dataset = datasets.get(DATASET_NAME, DATASET_VERSION)
    if dataset is None:
        print(f"dataset {DATASET_NAME}@{DATASET_VERSION} not found", file=sys.stderr)
        return 1

    fill = FillModel()
    if args.experiment == "buy-and-hold":
        strategy: BuyAndHold | Breakout = BuyAndHold()
        hypothesis = (
            "Baseline (docs/21 §21): buy-and-hold benchmark on BTCUSDT 1h over the "
            "official dataset. No improvement claim; reference point only."
        )
        start = None
        lookback = None
        params: dict[str, object] = {}
        slug = "buy-and-hold-btc-1h"
    else:
        strategy = Breakout(args.n)
        hypothesis = (
            f"Baseline (docs/21 §21): naive {args.n}-candle breakout on BTCUSDT 1h "
            "(close above the highest high of the N candles strictly before the "
            "decision candle -> long; below their lowest low -> flat). Fixed N, "
            "no optimization, no improvement claim."
        )
        # start after one window so warm-up genuinely seeds the indicator
        start = dataset.start_time + args.n * TIMEFRAME.duration
        lookback = args.n * TIMEFRAME.duration
        params = {"n": args.n}
        slug = f"breakout{args.n}-btc-1h"

    clock = SimulatedClock(start or dataset.start_time)
    events = replay_candles(
        PostgresCandleSnapshotFactory(url),
        datasets,
        SeriesResolver(PostgresVenueRepository(url), PostgresInstrumentRepository(url)),
        PostgresDataQualityEventRepository(url),
        PostgresAuditEventWriter(url),
        DATASET_NAME,
        DATASET_VERSION,
        clock,
        symbols=[SYMBOL],
        timeframes=[TIMEFRAME],
        start=start,
        lookback=lookback,
    )
    result = run_experiment(events, strategy, fill)

    created_at = utc_now()
    experiment_id = next_experiment_id(created_at.strftime("%Y%m%d"))
    out_dir = EXPERIMENTS_DIR / f"{experiment_id}-{slug}"
    out_dir.mkdir(parents=True, exist_ok=False)

    with (out_dir / "equity.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["close_time", "equity", "position"])
        cent = Decimal("0.01")
        for close_time, equity, position in result.equity_rows:
            writer.writerow([close_time.isoformat(), str(equity.quantize(cent)), position])

    record = {
        "experiment_id": experiment_id,
        "title": f"Baseline {args.experiment} {SYMBOL} {TIMEFRAME.value}",
        "status": "COMPLETED",
        "owner": "quantlab",
        "created_at": created_at.isoformat(),
        "hypothesis": hypothesis,
        "experiment_type": "baseline",
        "strategy_version": None,
        "code_commit": code_commit(),
        "dataset_version": f"{DATASET_NAME}@{DATASET_VERSION}",
        "dataset_content_hash": dataset.content_hash,
        "config_version": None,
        "feature_version": None,
        "model_version": None,
        "prompt_version": None,
        "parent_experiment_id": None,
        "baseline_experiment_id": None,
        "config": {
            "symbol": SYMBOL,
            "timeframe": TIMEFRAME.value,
            "start": (start or dataset.start_time).isoformat(),
            "end": dataset.end_time.isoformat(),
            "lookback_hours": args.n if lookback else None,
            "params": params,
            "fill_model": fill.as_record(),
        },
        "metrics": result.metrics(),
        "acceptance_criteria": "none — baseline, recorded as reference only",
        "results": "see metrics and equity.csv",
        "decision": "N/A (baseline; no conclusion is drawn, docs/21 §22)",
        "artifacts": ["equity.csv"],
        "notes": "T7bis: first real replay consumer; clock ended at " + clock.now().isoformat(),
    }
    (out_dir / "experiment.json").write_text(json.dumps(record, indent=2) + "\n")

    print(f"recorded {out_dir.name}")
    for key, value in result.metrics().items():
        print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

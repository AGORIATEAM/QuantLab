"""Execute EXP-20260901-003 (H1) over the pre-registered windows.

Usage:
    python scripts/run_h1.py --period insample
    python scripts/run_h1.py --period oos

Writes experiments/EXP-20260901-003-h1-structure-alignment/
<period>_<symbol>_metrics.csv (one row per configuration of the declared
neighborhoods) and prints a per-instrument summary. In-sample FIRST; the
out-of-sample window runs ONCE and is never re-cut (ADR-0002 décision 5).
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from itertools import product
from pathlib import Path
from statistics import median

from quantlab.core.clock import SimulatedClock
from quantlab.core.config import AppConfig
from quantlab.core.logging import configure_logging
from quantlab.data.datasets import SeriesResolver
from quantlab.data.replay import replay_candles
from quantlab.domain.models import Timeframe
from quantlab.research.baseline import FillModel
from quantlab.research.h1 import H1Config, H1Metrics, H1Simulator
from quantlab.storage.postgres.adapter import (
    PostgresAuditEventWriter,
    PostgresCandleSnapshotFactory,
    PostgresDataQualityEventRepository,
    PostgresDatasetRepository,
    PostgresInstrumentRepository,
    PostgresVenueRepository,
)
from quantlab.structure.engine import MarketStructureEngine
from quantlab.structure.state import StructureState

DATASET = ("btc-eth-spot-binance", "v1")
EXP_DIR = (
    Path(__file__).resolve().parent.parent
    / "experiments"
    / "EXP-20260901-003-h1-structure-alignment"
)
WINDOWS = {
    "insample": (datetime(2017, 8, 17, tzinfo=UTC), datetime(2023, 1, 1, tzinfo=UTC)),
    "oos": (datetime(2023, 1, 1, tzinfo=UTC), datetime(2026, 8, 30, tzinfo=UTC)),
}
# declared neighborhoods (experiment.json, amended 2026-09-01)
N_5M = [2, 3]
N_1H = [3, 5, 8]
MULTS = [Decimal("1.5"), Decimal("2"), Decimal("3")]
BUFFERS = [Decimal("0"), Decimal("0.1")]
R_TARGETS = [Decimal("1.5"), Decimal("2"), Decimal("3")]
MIN_STOPS = [Decimal("0"), Decimal("0.5")]

FIELDS = [
    "n_5m",
    "n_1h",
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
    "pct_time_neutral_1h",
    "h1_state_changes_per_week",
]


class ContextStats:
    """Per 1h-engine context statistics (post-ready decision candles)."""

    def __init__(self) -> None:
        self.bars = 0
        self.neutral_bars = 0
        self.changes = 0
        self._previous: StructureState | None = None

    def observe(self, state: StructureState) -> None:
        if state is StructureState.UNKNOWN:
            return  # not ready yet
        self.bars += 1
        if state is StructureState.NEUTRAL:
            self.neutral_bars += 1
        if self._previous is not None and state is not self._previous:
            self.changes += 1
        self._previous = state


def run_symbol(url: str, symbol: str, period: str) -> list[dict[str, object]]:
    start, end = WINDOWS[period]
    days = (end - start).days
    datasets = PostgresDatasetRepository(url)
    resolve = SeriesResolver(PostgresVenueRepository(url), PostgresInstrumentRepository(url))

    engines_5m: dict[tuple, MarketStructureEngine] = {}
    engines_1h: dict[tuple, MarketStructureEngine] = {}
    stats_1h: dict[tuple, ContextStats] = {}
    for n, mult, buf in product(N_5M, MULTS, BUFFERS):
        cfg = H1Config(n, 0, mult, buf, Decimal(1), Decimal(0))
        engines_5m[(n, mult, buf)] = MarketStructureEngine(cfg.engine_config(n))
    for n, mult, buf in product(N_1H, MULTS, BUFFERS):
        cfg = H1Config(0, n, mult, buf, Decimal(1), Decimal(0))
        engines_1h[(n, mult, buf)] = MarketStructureEngine(cfg.engine_config(n))
        stats_1h[(n, mult, buf)] = ContextStats()

    fill = FillModel()
    sims: list[H1Simulator] = []
    key_5m = key_1h = None
    started = time.monotonic()
    events_seen = 0

    stream = replay_candles(
        PostgresCandleSnapshotFactory(url),
        datasets,
        resolve,
        PostgresDataQualityEventRepository(url),
        PostgresAuditEventWriter(url),
        *DATASET,
        SimulatedClock(start),
        symbols=[symbol],
        timeframes=[Timeframe.M5, Timeframe.H1],
        start=start,
        end=end,
        lookback=timedelta(days=30),
    )
    for event in stream:
        events_seen += 1
        timeframe = event.series.timeframe
        if timeframe is Timeframe.H1:
            if key_1h is None:
                key_1h = event.series
            for key, engine in engines_1h.items():
                engine.on_event(event)
                if not event.is_warmup:
                    stats_1h[key].observe(engine.state_of(event.series))
            continue
        if key_5m is None:
            key_5m = event.series
            if key_1h is None:  # 1h key is deterministic from the 5m one
                key_1h = type(event.series)(
                    venue=event.series.venue,
                    venue_symbol=event.series.venue_symbol,
                    timeframe=Timeframe.H1,
                    source=event.series.source,
                )
            for n5, n1, mult, buf, r, ms in product(
                N_5M, N_1H, MULTS, BUFFERS, R_TARGETS, MIN_STOPS
            ):
                config = H1Config(n5, n1, mult, buf, r, ms)
                sims.append(
                    H1Simulator(
                        config,
                        engines_5m[(n5, mult, buf)],
                        engines_1h[(n1, mult, buf)],
                        key_5m,
                        key_1h,
                        fill,
                    )
                )
        outs = {key: engine.on_event(event) for key, engine in engines_5m.items()}
        for sim in sims:
            c = sim.config
            sim.on_5m(event, outs[(c.n_5m, c.atr_multiplier, c.breakout_buffer)])

    rows = []
    for sim in sims:
        metrics = sim.finalize()
        c = sim.config
        context = stats_1h[(c.n_1h, c.atr_multiplier, c.breakout_buffer)]
        rows.append(as_row(c, metrics, context, days, fill))
    elapsed = time.monotonic() - started
    print(f"{symbol} {period}: {events_seen} events, {len(sims)} configs, {elapsed / 60:.1f} min")
    return rows


def as_row(
    c: H1Config, m: H1Metrics, context: ContextStats, days: int, fill: FillModel
) -> dict[str, object]:
    trades = m.trades
    q = lambda v: str(Decimal(v).quantize(Decimal("0.0001")))  # noqa: E731
    return {
        "n_5m": c.n_5m,
        "n_1h": c.n_1h,
        "atr_mult": str(c.atr_multiplier),
        "buffer": str(c.breakout_buffer),
        "r_target": str(c.r_target),
        "min_stop_atr": str(c.min_stop_atr),
        "trades": trades,
        "expectancy_r": q(m.sum_r / trades) if trades else "",
        "profit_factor": q(m.gross_profit / m.gross_loss) if m.gross_loss > 0 else "",
        "win_rate_pct": q(Decimal(m.wins) / trades * 100) if trades else "",
        "max_drawdown_pct": q(m.max_drawdown_pct),
        "net_return_pct": q((m.final_equity / fill.initial_capital - 1) * 100),
        "fees_paid": q(m.fees_paid),
        "exposure_pct": q(Decimal(m.bars_in_position) / m.bars * 100) if m.bars else "",
        "sharpe_annualized": round(m.sharpe_annualized, 3) if m.sharpe_annualized else "",
        "avg_cost_r": q(m.sum_cost_r / trades) if trades else "",
        "avg_stop_pct": q(m.sum_stop_pct / trades) if trades else "",
        "trades_per_day": q(Decimal(trades) / days),
        "capped_share_pct": q(Decimal(m.capped) / trades * 100) if trades else "",
        "skipped_min_stop": m.skipped_min_stop,
        "ignored_in_position": m.ignored_in_position,
        "pct_time_neutral_1h": (
            q(Decimal(context.neutral_bars) / context.bars * 100) if context.bars else ""
        ),
        "h1_state_changes_per_week": (q(Decimal(context.changes) / days * 7) if days else ""),
    }


def summarize(symbol: str, rows: list[dict[str, object]]) -> None:
    expectancies = [float(r["expectancy_r"]) for r in rows if r["expectancy_r"] != ""]
    pfs = [float(r["profit_factor"]) for r in rows if r["profit_factor"] != ""]
    if not expectancies:
        print(f"  {symbol}: no trades at all")
        return
    positives = sum(1 for e in expectancies if e > 0)
    print(
        f"  {symbol}: expectancy_r median {median(expectancies):+.3f} "
        f"[min {min(expectancies):+.3f}, max {max(expectancies):+.3f}], "
        f"PF median {median(pfs):.3f}, configs>0: {positives}/{len(expectancies)}"
    )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--period", required=True, choices=["insample", "oos"])
    parser.add_argument("--symbols", default="BTCUSDT,ETHUSDT")
    args = parser.parse_args(argv)
    url = os.environ.get("QUANTLAB_DATABASE_URL")
    if not url:
        print("QUANTLAB_DATABASE_URL is not set", file=sys.stderr)
        return 2
    configure_logging(AppConfig.load().log_level)

    print(f"== EXP-20260901-003 {args.period} ==")
    for symbol in args.symbols.split(","):
        symbol = symbol.strip()
        rows = run_symbol(url, symbol, args.period)
        out = EXP_DIR / f"{args.period}_{symbol}_metrics.csv"
        with out.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        print(f"  wrote {out.name} ({len(rows)} configs)")
        summarize(symbol, rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

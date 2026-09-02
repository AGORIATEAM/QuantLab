"""Descriptive sweep frequency over 2024 (no profitability metrics).

Mechanical definition — bullish sweep: WICK_BREAK of a confirmed 5m swing
LOW (wick below the level, close back above — exactly the engine's
WICK_BREAK on the LOW side) while the slow context is BULLISH; bearish
sweep symmetric (HIGH-side WICK_BREAK while context BEARISH).

Counting unit: WICK_BREAK is emitted at most once per armed swing (MSE
design), so the table counts SWEPT SWINGS, not wicking candles — the
natural unit for one potential Hyp-2 entry per swept level.

Rows: (context in {1h n=8, 4h n=5}) x (n_5m in {2,3}) x (detector fractal
vs ATR mult=2 — the detector applies to BOTH the 5m series and its
context). Uses the Decimal reference engines: the fast path deliberately
skips wick bookkeeping.

Usage: python scripts/sweep_frequency.py
"""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime
from decimal import Decimal
from itertools import product

from quantlab.core.clock import SimulatedClock
from quantlab.core.config import AppConfig
from quantlab.core.logging import configure_logging
from quantlab.data.datasets import SeriesResolver
from quantlab.data.replay import replay_candles
from quantlab.domain.models import Timeframe
from quantlab.storage.postgres.adapter import (
    PostgresAuditEventWriter,
    PostgresCandleSnapshotFactory,
    PostgresDataQualityEventRepository,
    PostgresDatasetRepository,
    PostgresInstrumentRepository,
    PostgresVenueRepository,
)
from quantlab.structure.breaks import BreakDirection, BreakKind, ValidationMethod
from quantlab.structure.engine import (
    DetectorKind,
    MarketStructureEngine,
    StructureConfig,
    StructureEventType,
)
from quantlab.structure.state import StructureState

DATASET = ("btc-eth-spot-binance", "v1")
YEAR = (datetime(2024, 1, 1, tzinfo=UTC), datetime(2025, 1, 1, tzinfo=UTC))
DAYS = (YEAR[1] - YEAR[0]).days
CONTEXTS = {Timeframe.H1: 8, Timeframe.H4: 5}  # context tf -> n
N_5M = [2, 3]
DETECTORS = [(DetectorKind.FRACTAL, None), (DetectorKind.ATR, Decimal("2"))]


def engine(detector: DetectorKind, n: int, mult: Decimal | None) -> MarketStructureEngine:
    return MarketStructureEngine(
        StructureConfig(
            detector=detector,
            n=n,
            atr_multiplier=mult if mult is not None else Decimal("2"),
            validation=ValidationMethod.CLOSE,
        )
    )


def measure(url: str, symbol: str, context_tf: Timeframe) -> dict[tuple, tuple[int, int]]:
    """(detector, n_5m) -> (bullish_sweeps, bearish_sweeps)."""
    datasets = PostgresDatasetRepository(url)
    resolve = SeriesResolver(PostgresVenueRepository(url), PostgresInstrumentRepository(url))
    n_ctx = CONTEXTS[context_tf]
    context_engines = {d: engine(d, n_ctx, mult) for d, mult in DETECTORS}
    five_engines = {(d, n): engine(d, n, mult) for (d, mult), n in product(DETECTORS, N_5M)}
    counts: dict[tuple, list[int]] = {key: [0, 0] for key in five_engines}
    context_key = None

    for event in replay_candles(
        PostgresCandleSnapshotFactory(url),
        datasets,
        resolve,
        PostgresDataQualityEventRepository(url),
        PostgresAuditEventWriter(url),
        *DATASET,
        SimulatedClock(YEAR[0]),
        symbols=[symbol],
        timeframes=[Timeframe.M5, context_tf],
        start=YEAR[0],
        end=YEAR[1],
    ):
        if event.series.timeframe is context_tf:
            context_key = event.series
            for ctx in context_engines.values():
                ctx.on_event(event)
            continue
        for (d, n), eng in five_engines.items():
            outs = eng.on_event(event)
            if context_key is None:
                continue
            state = context_engines[d].state_of(context_key)
            for out in outs:
                if out.event_type is not StructureEventType.STRUCTURE_BREAK or out.brk is None:
                    continue
                if out.brk.kind is not BreakKind.WICK_BREAK:
                    continue
                if out.brk.direction is BreakDirection.BEARISH and state is StructureState.BULLISH:
                    counts[(d, n)][0] += 1  # low swept, bullish context
                elif (
                    out.brk.direction is BreakDirection.BULLISH and state is StructureState.BEARISH
                ):
                    counts[(d, n)][1] += 1  # high swept, bearish context
    return {key: (c[0], c[1]) for key, c in counts.items()}


def main(argv: list[str]) -> int:
    url = os.environ.get("QUANTLAB_DATABASE_URL")
    if not url:
        print("QUANTLAB_DATABASE_URL is not set", file=sys.stderr)
        return 2
    configure_logging(AppConfig.load().log_level)

    print("== 2024 sweep frequency (descriptive; ATR detector mult=2; no profitability) ==")
    print(
        f"{'symbol':<9}{'context':<10}{'detector':<10}{'n_5m':>5}"
        f"{'bull/day':>10}{'bear/day':>10}{'total/day':>10}"
    )
    for symbol in ("BTCUSDT", "ETHUSDT"):
        for context_tf, n_ctx in CONTEXTS.items():
            results = measure(url, symbol, context_tf)
            for (d, n), (bull, bear) in sorted(
                results.items(), key=lambda kv: (kv[0][0], kv[0][1])
            ):
                print(
                    f"{symbol:<9}{context_tf.value + f' n={n_ctx}':<10}{d.value:<10}{n:>5}"
                    f"{bull / DAYS:>10.2f}{bear / DAYS:>10.2f}{(bull + bear) / DAYS:>10.2f}"
                )
    print("\nCounting unit: swept swings (one WICK_BREAK max per armed swing).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

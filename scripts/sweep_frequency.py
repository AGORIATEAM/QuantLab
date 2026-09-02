"""Descriptive counter-context sweep measurement (no profitability).

Mechanical definition — bullish sweep: WICK_BREAK of a confirmed decision-
timeframe swing LOW (wick below the level, recovery close intrinsic) while
the slow context is BULLISH; bearish symmetric. Counting unit: swept
swings (one WICK_BREAK max per armed swing).

Also reports the STOP DISTANCE each sweep would offer — wick extreme to
recovery close, in % of price (median, q25, q75): the variable that killed
Hyp-2 at 5m, measured BEFORE anything gets frozen.

Detectors apply to BOTH stages (decision series and its context); the ATR
variant uses mult=2. Decimal reference engines (the fast path skips wick
bookkeeping by design). Counting starts after the warm-up window.

Usage:
    python scripts/sweep_frequency.py                       # original 5m table
    python scripts/sweep_frequency.py --decision 15m \
        --contexts 4h:5,1d:3 --lookback-days 120            # Hyp-3 step
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from itertools import product
from statistics import median, quantiles

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


def measure(
    url: str,
    symbol: str,
    decision_tf: Timeframe,
    context_tf: Timeframe,
    n_context: int,
    n_decisions: list[int],
    lookback_days: int,
) -> dict[tuple, tuple[int, int, list[float]]]:
    """(detector, n_decision) -> (bull_sweeps, bear_sweeps, stop_distances_%)."""
    datasets = PostgresDatasetRepository(url)
    resolve = SeriesResolver(PostgresVenueRepository(url), PostgresInstrumentRepository(url))
    context_engines = {d: engine(d, n_context, mult) for d, mult in DETECTORS}
    decision_engines = {
        (d, n): engine(d, n, mult) for (d, mult), n in product(DETECTORS, n_decisions)
    }
    counts: dict[tuple, tuple[list[int], list[float]]] = {
        key: ([0, 0], []) for key in decision_engines
    }
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
        timeframes=[decision_tf, context_tf],
        start=YEAR[0],
        end=YEAR[1],
        lookback=timedelta(days=lookback_days) if lookback_days else None,
    ):
        if event.series.timeframe is context_tf:
            context_key = event.series
            for ctx in context_engines.values():
                ctx.on_event(event)
            continue
        close = event.candle.close
        for (d, n), eng in decision_engines.items():
            outs = eng.on_event(event)
            if context_key is None or event.is_warmup:
                continue  # warm-up seeds the engines; the year alone is counted
            state = context_engines[d].state_of(context_key)
            for out in outs:
                if out.event_type is not StructureEventType.STRUCTURE_BREAK or out.brk is None:
                    continue
                if out.brk.kind is not BreakKind.WICK_BREAK:
                    continue
                pair, distances = counts[(d, n)]
                if out.brk.direction is BreakDirection.BEARISH and state is StructureState.BULLISH:
                    pair[0] += 1
                elif (
                    out.brk.direction is BreakDirection.BULLISH and state is StructureState.BEARISH
                ):
                    pair[1] += 1
                else:
                    continue
                distances.append(float(abs(close - out.brk.break_price) / close * 100))
    return {key: (c[0][0], c[0][1], c[1]) for key, c in counts.items()}


def parse_contexts(raw: str) -> list[tuple[Timeframe, int]]:
    out = []
    for part in raw.split(","):
        tf, n = part.strip().split(":")
        out.append((Timeframe(tf), int(n)))
    return out


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision", default="5m", choices=["5m", "15m"])
    parser.add_argument("--contexts", default="1h:8,4h:5", help="tf:n comma-separated")
    parser.add_argument("--n-decisions", default="2,3")
    parser.add_argument("--lookback-days", type=int, default=0)
    args = parser.parse_args(argv)
    url = os.environ.get("QUANTLAB_DATABASE_URL")
    if not url:
        print("QUANTLAB_DATABASE_URL is not set", file=sys.stderr)
        return 2
    configure_logging(AppConfig.load().log_level)
    decision_tf = Timeframe(args.decision)
    contexts = parse_contexts(args.contexts)
    n_decisions = [int(n) for n in args.n_decisions.split(",")]

    print(
        f"== 2024 counter-context sweeps on {decision_tf.value} structure "
        f"(descriptive; ATR mult=2; stop = wick extreme -> recovery close) =="
    )
    print(
        f"{'symbol':<9}{'context':<10}{'detector':<10}{'n':>3}"
        f"{'bull/d':>8}{'bear/d':>8}{'tot/d':>8}"
        f"{'stop% med':>11}{'q25':>8}{'q75':>8}"
    )
    for symbol in ("BTCUSDT", "ETHUSDT"):
        for context_tf, n_ctx in contexts:
            results = measure(
                url, symbol, decision_tf, context_tf, n_ctx, n_decisions, args.lookback_days
            )
            for (d, n), (bull, bear, dists) in sorted(
                results.items(), key=lambda kv: (kv[0][0], kv[0][1])
            ):
                if dists:
                    q25, _q50, q75 = quantiles(dists, n=4)
                    med = median(dists)
                    stats = f"{med:>11.3f}{q25:>8.3f}{q75:>8.3f}"
                else:
                    stats = f"{'-':>11}{'-':>8}{'-':>8}"
                print(
                    f"{symbol:<9}{context_tf.value + f' n={n_ctx}':<10}{d.value:<10}{n:>3}"
                    f"{bull / DAYS:>8.2f}{bear / DAYS:>8.2f}{(bull + bear) / DAYS:>8.2f}{stats}"
                )
    print("\nCounting unit: swept swings (one WICK_BREAK max per armed swing);")
    print("distances measured at the recovery close, warm-up excluded from counting.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

"""Descriptive counter-context sweep measurement (no profitability).

Mechanical definition — bullish sweep: WICK_BREAK of a confirmed decision-
timeframe swing LOW (wick below the level, recovery close intrinsic) while
the slow context is BULLISH; bearish symmetric. Counting unit: swept
swings (one WICK_BREAK max per armed swing).

Also reports the STOP DISTANCE each sweep would offer — wick extreme to
recovery close, in % of price (median, q25, q75): the variable that killed
Hyp-2 at 5m, measured BEFORE anything gets frozen.

--stop-table renders the same events under three candidate stop
definitions (calibration step before Hyp-3): (c) wick extreme alone;
(a_k) max(wick extreme, k x ATR of the decision timeframe) for k in
{2,3,4}; (b) the last confirmed OPPOSITE swing PRIOR to the swept one —
the swept level itself is excluded by construction: the wick already
violated it, a stop there would be tighter than the wick. Implicit cost
in R = 0.22% round-trip floor / distance; cost quantiles map exactly from
distance quantiles (monotone inverse).

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
from quantlab.structure.swings import SwingKind

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
) -> dict[tuple, tuple[int, int, list[tuple[float, float, float | None]]]]:
    """(detector, n_decision) -> (bull, bear, events) where each event is
    (wick_distance_%, atr_%_of_price, prev_opposite_swing_distance_%|None)."""
    datasets = PostgresDatasetRepository(url)
    resolve = SeriesResolver(PostgresVenueRepository(url), PostgresInstrumentRepository(url))
    context_engines = {d: engine(d, n_context, mult) for d, mult in DETECTORS}
    decision_engines = {
        (d, n): engine(d, n, mult) for (d, mult), n in product(DETECTORS, n_decisions)
    }
    counts: dict[tuple, tuple[list[int], list[tuple[float, float, float | None]]]] = {
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
                pair, events = counts[(d, n)]
                if out.brk.direction is BreakDirection.BEARISH and state is StructureState.BULLISH:
                    pair[0] += 1
                    long_side = True
                elif (
                    out.brk.direction is BreakDirection.BULLISH and state is StructureState.BEARISH
                ):
                    pair[1] += 1
                    long_side = False
                else:
                    continue
                wick_pct = float(abs(close - out.brk.break_price) / close * 100)
                runtime = eng.runtime(event.series)
                atr_value = runtime.detector.atr.value
                atr_pct = float(atr_value / close * 100) if atr_value is not None else 0.0
                # (b): last confirmed OPPOSITE swing PRIOR to the swept one —
                # the swept level itself is excluded (the wick already broke it)
                stop_kind = SwingKind.LOW if long_side else SwingKind.HIGH
                same_kind = [sw for sw in runtime.sequence.swings if sw.kind is stop_kind]
                prev_pct: float | None = None
                if len(same_kind) >= 2:
                    prev_price = same_kind[-2].price
                    signed = (close - prev_price) if long_side else (prev_price - close)
                    if signed > 0:  # a stop on the wrong side of price is no stop
                        prev_pct = float(signed / close * 100)
                events.append((wick_pct, atr_pct, prev_pct))
    return {key: (c[0][0], c[0][1], c[1]) for key, c in counts.items()}


COST_FLOOR_PCT = 0.22  # round-trip cost floor (ADR-0002 décision 2 / addendum C)
TARGET_MED_R, TARGET_Q75_R = 0.2, 0.35  # calibration target being located


def render_stop_table(label: str, bull: int, bear: int, events: list) -> None:
    total = bull + bear
    atr_med = median([e[1] for e in events]) if events else 0.0
    print(f"{label}  sweeps/j={total / DAYS:.2f}  ATR_med%={atr_med:.3f}")
    definitions: list[tuple[str, list[float]]] = [
        ("c: meche seule", [e[0] for e in events]),
    ]
    for k in (2, 3, 4):
        definitions.append((f"a: max(meche,{k}xATR)", [max(e[0], k * e[1]) for e in events]))
    covered = [e[2] for e in events if e[2] is not None]
    definitions.append((f"b: swing oppose prec. ({len(covered)}/{len(events)})", covered))
    for name, dists in definitions:
        if len(dists) < 4:
            print(f"    {name:<28} (insufficient events)")
            continue
        q25, _q50, q75 = quantiles(dists, n=4)
        med = median(dists)
        cost_med = COST_FLOOR_PCT / med
        cost_q25 = COST_FLOOR_PCT / q75  # best quartile of cost
        cost_q75 = COST_FLOOR_PCT / q25  # worst quartile of cost
        ok = "  <- CIBLE" if cost_med <= TARGET_MED_R and cost_q75 <= TARGET_Q75_R else ""
        print(
            f"    {name:<28} dist% {med:6.3f} [{q25:6.3f};{q75:6.3f}]"
            f"   cout_R {cost_med:5.2f} [{cost_q25:5.2f};{cost_q75:5.2f}]{ok}"
        )


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
    parser.add_argument(
        "--stop-table", action="store_true", help="stop-definition calibration table"
    )
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
            for (d, n), (bull, bear, events) in sorted(
                results.items(), key=lambda kv: (kv[0][0], kv[0][1])
            ):
                label = f"{symbol:<9}{context_tf.value + f' n={n_ctx}':<10}{d.value:<10}{n:>3}"
                if args.stop_table:
                    render_stop_table(label, bull, bear, events)
                    continue
                dists = [e[0] for e in events]
                if dists:
                    q25, _q50, q75 = quantiles(dists, n=4)
                    stats = f"{median(dists):>11.3f}{q25:>8.3f}{q75:>8.3f}"
                else:
                    stats = f"{'-':>11}{'-':>8}{'-':>8}"
                daily = f"{bull / DAYS:>8.2f}{bear / DAYS:>8.2f}{(bull + bear) / DAYS:>8.2f}"
                print(f"{label}{daily}{stats}")
    print("\nCounting unit: swept swings (one WICK_BREAK max per armed swing);")
    print("distances measured at the recovery close, warm-up excluded from counting.")
    if args.stop_table:
        print(
            f"cout_R = {COST_FLOOR_PCT}% / distance ; quantiles du cout par transformee inverse "
            f"exacte ; CIBLE: cout med <= {TARGET_MED_R} R ET q75 <= {TARGET_Q75_R} R."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

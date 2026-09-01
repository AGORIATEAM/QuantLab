"""Market Structure Engine demo on the official dataset — NO trading.

1. Streams a short window (first week of 2024, BTCUSDT 1h) through the
   engine and prints structure events with both timestamps.
2. Density table over 2024 per (timeframe, detector, n[, atr_mult]) using
   the H1 neighborhoods (EXP-20260901-003): swings/day and BOS/day.
   DESCRIPTIVE ONLY — no parameter choice follows from this table without
   discussion (validation: close, buffer 0).

Usage:
    python scripts/structure_demo.py [--symbol BTCUSDT]
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import UTC, datetime
from decimal import Decimal

from quantlab.core.clock import SimulatedClock
from quantlab.core.config import AppConfig
from quantlab.core.logging import configure_logging
from quantlab.data.datasets import SeriesResolver
from quantlab.data.replay import ReplayEvent, replay_candles
from quantlab.domain.models import Timeframe
from quantlab.storage.postgres.adapter import (
    PostgresAuditEventWriter,
    PostgresCandleSnapshotFactory,
    PostgresDataQualityEventRepository,
    PostgresDatasetRepository,
    PostgresInstrumentRepository,
    PostgresVenueRepository,
)
from quantlab.structure.breaks import BreakKind
from quantlab.structure.engine import (
    DetectorKind,
    MarketStructureEngine,
    StructureConfig,
    StructureEventType,
)

DATASET = ("btc-eth-spot-binance", "v1")
YEAR_START = datetime(2024, 1, 1, tzinfo=UTC)
YEAR_END = datetime(2025, 1, 1, tzinfo=UTC)
DAYS = (YEAR_END - YEAR_START).days
# H1 neighborhoods (EXP-20260901-003)
N_BY_TF = {Timeframe.M5: [2, 3], Timeframe.H1: [3, 5]}
ATR_MULTS = [Decimal("1.5"), Decimal("2"), Decimal("3")]


def collect_events(url: str, symbol: str, timeframe: Timeframe) -> list[ReplayEvent]:
    datasets = PostgresDatasetRepository(url)
    resolve = SeriesResolver(PostgresVenueRepository(url), PostgresInstrumentRepository(url))
    return list(
        replay_candles(
            PostgresCandleSnapshotFactory(url),
            datasets,
            resolve,
            PostgresDataQualityEventRepository(url),
            PostgresAuditEventWriter(url),
            *DATASET,
            SimulatedClock(YEAR_START),
            symbols=[symbol],
            timeframes=[timeframe],
            start=YEAR_START,
            end=YEAR_END,
        )
    )


def show_window(events: list[ReplayEvent], limit: int = 12) -> None:
    engine = MarketStructureEngine(StructureConfig(detector=DetectorKind.FRACTAL, n=3))
    shown = 0
    for event in events:
        for out in engine.on_event(event):
            if shown >= limit:
                return
            shown += 1
            what = out.event_type.value
            if out.brk is not None:
                what = f"{out.brk.kind.value} {out.brk.direction.value} @ {out.brk.level}"
            elif out.swing is not None:
                what = f"SWING {out.swing.kind.value} @ {out.swing.price}"
            print(
                f"  {what:<38} state={out.state.value:<8} "
                f"event={out.event_timestamp.isoformat()} "
                f"available_at={out.available_at.isoformat()}"
            )


def densities(events: list[ReplayEvent], config: StructureConfig) -> tuple[float, float]:
    engine = MarketStructureEngine(config)
    swings = bos = 0
    for event in events:
        for out in engine.on_event(event):
            if out.event_type is StructureEventType.SWING_CONFIRMED:
                swings += 1
            elif out.brk is not None and out.brk.kind is BreakKind.BOS:
                bos += 1
    return swings / DAYS, bos / DAYS


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbol", default="BTCUSDT")
    args = parser.parse_args(argv)
    url = os.environ.get("QUANTLAB_DATABASE_URL")
    if not url:
        print("QUANTLAB_DATABASE_URL is not set", file=sys.stderr)
        return 2
    configure_logging(AppConfig.load().log_level)

    print(f"== sample events: {args.symbol} 1h, first week of 2024 (fractal n=3) ==")
    hourly = collect_events(url, args.symbol, Timeframe.H1)
    week = [e for e in hourly if e.candle.close_time <= datetime(2024, 1, 8, tzinfo=UTC)]
    show_window(week)

    print(f"\n== 2024 densities, {args.symbol} (validation close, buffer 0 — descriptive only) ==")
    print(
        f"{'timeframe':<10}{'detector':<10}{'n':>3}{'atr_mult':>9}{'swings/day':>12}{'BOS/day':>9}"
    )
    for timeframe in (Timeframe.M5, Timeframe.H1):
        events = (
            hourly if timeframe is Timeframe.H1 else collect_events(url, args.symbol, timeframe)
        )
        for n in N_BY_TF[timeframe]:
            rows: list[tuple[StructureConfig, str]] = [
                (StructureConfig(detector=DetectorKind.FRACTAL, n=n), "-")
            ]
            rows += [
                (
                    StructureConfig(detector=DetectorKind.ATR, n=n, atr_multiplier=m),
                    str(m),
                )
                for m in ATR_MULTS
            ]
            for config, mult_label in rows:
                swings_per_day, bos_per_day = densities(events, config)
                print(
                    f"{timeframe.value:<10}{config.detector.value:<10}{n:>3}{mult_label:>9}"
                    f"{swings_per_day:>12.1f}{bos_per_day:>9.1f}"
                )
    print("\nNo parameter choice follows from this table without discussion.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

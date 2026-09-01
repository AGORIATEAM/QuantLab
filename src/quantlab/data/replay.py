"""Replay engine: deterministic, fail-closed candle streaming (T7,
ADR-0001 décision 6, docs/03 §40, roadmap §30).

Guarantees
==========

- **Fail-closed**: every consumed series is re-verified against its published
  dataset hash (``verify_series``) before a single candle is emitted; any
  divergence raises ReplayIntegrityError. The FULL per-series verification at
  startup is the Phase 1 rule — any optimization (count-only fast path, ...)
  is a Phase 2 decision to be made against the recorded benchmarks, not here.
- **Single snapshot**: verification AND the per-series streaming cursors all
  run inside one CandleSnapshotFactory context (PostgreSQL: one read-only
  REPEATABLE READ transaction). What was verified is exactly what streams,
  and concurrent inserts landing mid-replay are invisible.
- **Zero look-ahead**: events are emitted ordered by availability time
  (close_time), tie-broken by ascending timeframe duration then venue and
  symbol — a 1h candle closing at 13:00 is emitted after the 1m candle
  closing at 13:00 that it covers, and the order is total, hence the stream
  is deterministic. The SimulatedClock is advanced to each candle's
  close_time before emission: at any instant, nothing the consumer has seen
  closes after clock.now().
- **Warm-up**: with a lookback window, history candles (close_time <= start)
  are emitted first with the clock pinned at `start` and flagged
  ``is_warmup=True`` — indicators can seed themselves, and a consumer can
  never mistake warm-up for a decision-time candle.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta
from heapq import merge

from quantlab.audit.events import AuditEvent, AuditResult, service_event
from quantlab.core.clock import SimulatedClock
from quantlab.core.logging import get_logger
from quantlab.core.timeutils import require_utc
from quantlab.data.datasets import (
    DatasetError,
    SeriesMismatch,
    SeriesResolver,
    load_dataset_series,
    verify_series,
)
from quantlab.domain.models import Candle, Dataset, DatasetSeries, Instrument, Timeframe, Venue
from quantlab.storage.repositories import (
    AuditEventWriter,
    CandleRepository,
    CandleSnapshotFactory,
    DataQualityEventRepository,
    DatasetRepository,
)

logger = get_logger(__name__)

ACTOR_ID = "replay_candles"


class ReplayIntegrityError(Exception):
    """The dataset diverged from its published hash — nothing was streamed."""

    def __init__(self, dataset: str, mismatches: list[SeriesMismatch]) -> None:
        self.mismatches = mismatches
        detail = ", ".join(f"{m.venue_symbol}/{m.timeframe.value}:{m.kind}" for m in mismatches)
        super().__init__(f"replay refused, {dataset} diverged: {detail}")


@dataclass(frozen=True)
class ReplayEvent:
    """One emitted candle. is_warmup marks lookback history (close_time <=
    replay start): seeding material, never a decision-time candle."""

    candle: Candle
    is_warmup: bool


def replay_candles(
    snapshot_factory: CandleSnapshotFactory,
    datasets: DatasetRepository,
    resolve: SeriesResolver,
    quality: DataQualityEventRepository,
    audit: AuditEventWriter,
    dataset_name: str,
    version: str,
    clock: SimulatedClock,
    symbols: list[str] | None = None,
    timeframes: list[Timeframe] | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    lookback: timedelta | None = None,
) -> Iterator[ReplayEvent]:
    """Stream a published dataset's candles in availability order under a
    simulated clock. Generator: verification runs on first iteration; the
    snapshot is held until the generator is exhausted or closed."""
    dataset, entries = load_dataset_series(datasets, resolve, dataset_name, version)
    entries = _select(dataset, entries, symbols, timeframes)

    start = dataset.start_time if start is None else require_utc(start, "start")
    end = dataset.end_time if end is None else require_utc(end, "end")
    if not (dataset.start_time <= start < end <= dataset.end_time):
        raise ValueError(
            f"replay window [{start.isoformat()}, {end.isoformat()}) must sit inside "
            f"the dataset range [{dataset.start_time.isoformat()}, "
            f"{dataset.end_time.isoformat()})"
        )
    lookback_start = start if lookback is None else max(dataset.start_time, start - lookback)

    with snapshot_factory() as candles:
        verify_seconds = _verify_all(candles, datasets, resolve, quality, audit, dataset, entries)
        audit.write(
            _event(
                "REPLAY_STARTED",
                dataset,
                AuditResult.SUCCESS,
                {
                    "dataset_name": dataset.dataset_name,
                    "version": dataset.version,
                    "series": len(entries),
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                    "lookback_start": lookback_start.isoformat(),
                    "verify_seconds": round(verify_seconds, 3),
                },
            )
        )

        clock.advance_to(max(clock.now(), start))
        streams = [
            _series_stream(candles, venue, instrument, stored, lookback_start, end)
            for stored, venue, instrument in entries
        ]
        emitted = warmups = 0
        streamed_at = time.monotonic()
        try:
            for _key, candle in merge(*streams):
                is_warmup = candle.close_time <= start
                clock.advance_to(max(clock.now(), candle.close_time))
                warmups += is_warmup
                emitted += 1
                yield ReplayEvent(candle=candle, is_warmup=is_warmup)
        except Exception as exc:
            audit.write(
                _event(
                    "REPLAY_FAILED",
                    dataset,
                    AuditResult.FAILURE,
                    {"error": str(exc)[:500], "emitted": emitted},
                )
            )
            raise
        duration = time.monotonic() - streamed_at
        audit.write(
            _event(
                "REPLAY_COMPLETED",
                dataset,
                AuditResult.SUCCESS,
                {
                    "dataset_name": dataset.dataset_name,
                    "version": dataset.version,
                    "emitted": emitted,
                    "warmup": warmups,
                    "stream_seconds": round(duration, 3),
                    "candles_per_second": round(emitted / duration) if duration > 0 else None,
                },
            )
        )
        logger.info(
            "replay_completed",
            dataset=f"{dataset.dataset_name}@{dataset.version}",
            emitted=emitted,
            warmup=warmups,
            stream_seconds=round(duration, 3),
        )


def _select(
    dataset: Dataset,
    entries: list[tuple[DatasetSeries, Venue, Instrument]],
    symbols: list[str] | None,
    timeframes: list[Timeframe] | None,
) -> list[tuple[DatasetSeries, Venue, Instrument]]:
    if symbols is not None:
        unknown = set(symbols) - {e[0].venue_symbol for e in entries}
        if unknown:
            raise DatasetError(f"symbols {sorted(unknown)} are not part of the dataset")
    selected = [
        e
        for e in entries
        if (symbols is None or e[0].venue_symbol in symbols)
        and (timeframes is None or e[0].timeframe in timeframes)
    ]
    if not selected:
        raise DatasetError(
            f"selection matches no series of {dataset.dataset_name}@{dataset.version}"
        )
    return selected


def _verify_all(
    candles: CandleRepository,
    datasets: DatasetRepository,
    resolve: SeriesResolver,
    quality: DataQualityEventRepository,
    audit: AuditEventWriter,
    dataset: Dataset,
    entries: list[tuple[DatasetSeries, Venue, Instrument]],
) -> float:
    """Fail-closed gate: full verification of every consumed series, on the
    same snapshot the stream will read."""
    started = time.monotonic()
    mismatches: list[SeriesMismatch] = []
    for stored, _venue, _instrument in entries:
        report = verify_series(
            candles,
            datasets,
            resolve,
            quality,
            audit,
            dataset.dataset_name,
            dataset.version,
            stored.venue_symbol,
            stored.timeframe,
        )
        mismatches.extend(report.mismatches)
    if mismatches:
        audit.write(
            _event(
                "REPLAY_REFUSED",
                dataset,
                AuditResult.DENIED,
                {
                    "dataset_name": dataset.dataset_name,
                    "version": dataset.version,
                    "mismatches": [
                        f"{m.venue_symbol}/{m.timeframe.value}:{m.kind}" for m in mismatches
                    ],
                },
            )
        )
        raise ReplayIntegrityError(f"{dataset.dataset_name}@{dataset.version}", mismatches)
    return time.monotonic() - started


def _series_stream(
    candles: CandleRepository,
    venue: Venue,
    instrument: Instrument,
    stored: DatasetSeries,
    lookback_start: datetime,
    end: datetime,
) -> Iterator[tuple[tuple[datetime, timedelta, str, str], Candle]]:
    """One series as (sort_key, candle), already ordered: close_time is
    open_time + duration on a fixed grid, so open_time order IS close_time
    order within a series. Emits candles with close_time in
    (lookback_start, end]."""
    duration = stored.timeframe.duration
    fetch_start = lookback_start - duration + timedelta(milliseconds=1)
    for batch in candles.stream_candles(
        instrument.instrument_id, stored.timeframe, stored.source, fetch_start, end
    ):
        for candle in batch:
            if candle.close_time > end:
                continue  # a large-timeframe candle crossing the window end is not available yet
            yield (
                (candle.close_time, duration, venue.code, instrument.venue_symbol),
                candle,
            )


def _event(
    action: str,
    dataset: Dataset,
    result: AuditResult,
    metadata: dict[str, object],
) -> AuditEvent:
    return service_event(ACTOR_ID, action, "datasets", str(dataset.dataset_id), result, metadata)

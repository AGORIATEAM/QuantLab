"""Dataset registry: freeze and verify hash-checked candle selections (T6,
ADR-0001 décisions 2 et 6, docs/23 §150).

Canonical serialization ``qlds-v1`` — the exact hash input
=========================================================

SHA-256 over a stream of UTF-8 lines (each terminated by ``\\n``):

    D|qlds-v1
    S|{venue}|{venue_symbol}|{timeframe}|{source}|{start_iso}|{end_iso}
    C|{open_time_ms}|{open}|{high}|{low}|{close}|{volume}|{trade_count}

- One ``S`` line per series, followed by its ``C`` lines ordered by
  open_time; series are ordered by (venue, venue_symbol, timeframe, source)
  so the hash is independent of the order the caller listed them.
- The ``D`` line carries only the serialization version tag: the hash covers
  CONTENT only — the same selection frozen under a different dataset name or
  version yields the same content_hash. Name and version live in the table
  columns and metadata.
- Decimals are canonical fixed-point: no exponent, trailing zeros stripped,
  bare integer when the fraction is empty ("1.10"→"1.1", "1E+2"→"100",
  "0.00"→"0"). A NULL trade_count is rendered as ``-``.
- Excluded, and why: candle_id (surrogate, not content), close_time
  (derivable from open_time + timeframe, CHECK-constrained), instrument_id
  (environment-specific UUID — excluding it makes hashes portable across
  re-seeded databases; the series is identified by venue + venue_symbol +
  source), data_version (provenance metadata, always NULL in Phase 1; any
  venue rewrite shows up in the OHLCV itself).
- Each series also gets a sub-hash (same lines, ``D`` line included, only
  that series): verify can then name WHICH series diverged.

The golden test in tests/unit/test_datasets.py locks this format byte for
byte; any change requires a new tag (qlds-v2) and a new dataset version.

Fail-closed contract (ADR décision 6): ``verify_dataset`` /
``verify_series`` are what a consumer MUST run before reading a dataset —
T7's replay_candles calls verify at startup and refuses to stream on any
divergence. Verification pre-checks candle counts per series (cheap) and
only hashes when counts match.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from itertools import product
from typing import Any

from quantlab.audit.events import AuditEvent, AuditResult, service_event
from quantlab.core.ids import new_id
from quantlab.core.logging import get_logger
from quantlab.core.timeutils import require_utc, utc_now
from quantlab.domain.models import (
    DataQualityEvent,
    Dataset,
    DatasetSeries,
    Instrument,
    QualityCode,
    QualitySeverity,
    Timeframe,
    Venue,
)
from quantlab.storage.repositories import (
    AuditEventWriter,
    CandleRepository,
    DataQualityEventRepository,
    DatasetRepository,
    InstrumentRepository,
    VenueRepository,
)

logger = get_logger(__name__)

ACTOR_ID = "dataset_registry"
CANONICAL_VERSION = "qlds-v1"
_D_LINE = f"D|{CANONICAL_VERSION}\n".encode()


class DatasetError(Exception):
    """Freeze/verify failed for a structural reason (unknown dataset,
    duplicate publication, unresolvable series)."""


@dataclass(frozen=True)
class SeriesMismatch:
    venue_symbol: str
    timeframe: Timeframe
    kind: str  # "count" | "hash"
    expected: str
    actual: str


@dataclass(frozen=True)
class VerifyReport:
    dataset_name: str
    version: str
    ok: bool
    candle_count: int
    mismatches: list[SeriesMismatch]


def canonical_decimal(value: Decimal) -> str:
    """Fixed-point, no exponent, no trailing zeros ("1.10"→"1.1", "1E+2"→"100")."""
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _candle_line(row: tuple[Any, ...]) -> bytes:
    open_time, open_, high, low, close, volume, trade_count = row
    tc = "-" if trade_count is None else str(trade_count)
    return (
        f"C|{int(open_time.timestamp() * 1000)}"
        f"|{canonical_decimal(open_)}|{canonical_decimal(high)}"
        f"|{canonical_decimal(low)}|{canonical_decimal(close)}"
        f"|{canonical_decimal(volume)}|{tc}\n"
    ).encode()


def _series_line(
    venue: str, venue_symbol: str, timeframe: Timeframe, source: str, start: datetime, end: datetime
) -> bytes:
    return (
        f"S|{venue}|{venue_symbol}|{timeframe.value}|{source}"
        f"|{start.isoformat()}|{end.isoformat()}\n"
    ).encode()


def _sort_key(item: tuple[Venue, Instrument, Timeframe]) -> tuple[str, str, str]:
    venue, instrument, timeframe = item
    return (venue.code, instrument.venue_symbol, timeframe.value)


def _hash_series(
    candles: CandleRepository,
    venue: Venue,
    instrument: Instrument,
    timeframe: Timeframe,
    source: str,
    start: datetime,
    end: datetime,
    global_hash: hashlib._Hash | None,
) -> tuple[str, int]:
    """Stream one series into its own sub-hash (D line + S line + C lines)
    and, when given, into the dataset-wide hash. Returns (hex, count)."""
    series_hash = hashlib.sha256(_D_LINE)
    header = _series_line(venue.code, instrument.venue_symbol, timeframe, source, start, end)
    series_hash.update(header)
    if global_hash is not None:
        global_hash.update(header)
    count = 0
    for batch in candles.stream_candle_rows(
        instrument.instrument_id, timeframe, source, start, end
    ):
        for row in batch:
            line = _candle_line(row)
            series_hash.update(line)
            if global_hash is not None:
                global_hash.update(line)
        count += len(batch)
    return series_hash.hexdigest(), count


def freeze_dataset(
    candles: CandleRepository,
    datasets: DatasetRepository,
    audit: AuditEventWriter,
    dataset_name: str,
    version: str,
    selections: list[tuple[Venue, Instrument]],
    timeframes: list[Timeframe],
    start: datetime,
    end: datetime,
    source_name: str,
    code_commit: str | None = None,
) -> Dataset:
    """Compute the canonical hash of (selections x timeframes) over
    [start, end) and publish the dataset. Atomic: no draft state."""
    start = require_utc(start, "start")
    end = require_utc(end, "end")
    if end <= start:
        raise ValueError("end must be strictly after start")
    if not selections or not timeframes:
        raise DatasetError("a dataset needs at least one instrument and one timeframe")
    if datasets.get(dataset_name, version) is not None:
        raise DatasetError(f"dataset {dataset_name!r} version {version!r} is already published")

    entries = sorted(
        ((venue, instrument, tf) for (venue, instrument), tf in product(selections, timeframes)),
        key=_sort_key,
    )
    global_hash = hashlib.sha256(_D_LINE)
    series: list[DatasetSeries] = []
    total = 0
    for venue, instrument, timeframe in entries:
        series_hex, count = _hash_series(
            candles, venue, instrument, timeframe, source_name, start, end, global_hash
        )
        total += count
        series.append(
            DatasetSeries(
                venue=venue.code,
                venue_symbol=instrument.venue_symbol,
                timeframe=timeframe,
                source=source_name,
                start=start,
                end=end,
                candle_count=count,
                series_hash=series_hex,
            )
        )
        logger.info(
            "series_hashed",
            venue_symbol=instrument.venue_symbol,
            timeframe=timeframe.value,
            candles=count,
        )

    dataset = Dataset(
        dataset_id=new_id(),
        dataset_name=dataset_name,
        version=version,
        storage_uri=f"postgresql://quantlab/candles?dataset={dataset_name}@{version}",
        content_hash=global_hash.hexdigest(),
        source=source_name,
        start_time=start,
        end_time=end,
        metadata={
            "canonical_version": CANONICAL_VERSION,
            "code_commit": code_commit,
            "total_candles": total,
            "series": [s.model_dump(mode="json") for s in series],
        },
    )
    datasets.insert(dataset)
    audit.write(
        _event(
            "DATASET_FROZEN",
            dataset,
            AuditResult.SUCCESS,
            {
                "dataset_name": dataset_name,
                "version": version,
                "content_hash": dataset.content_hash,
                "series": len(series),
                "total_candles": total,
                "code_commit": code_commit,
            },
        )
    )
    return dataset


def verify_dataset(
    candles: CandleRepository,
    datasets: DatasetRepository,
    resolve: SeriesResolver,
    quality: DataQualityEventRepository,
    audit: AuditEventWriter,
    dataset_name: str,
    version: str,
) -> VerifyReport:
    """Fail-closed integrity check: per-series candle counts first (cheap —
    any late insertion or deletion fails here without hashing), then the
    per-series hashes, then the global hash by construction."""
    dataset, entries = _load(datasets, resolve, dataset_name, version)
    mismatches = _check_counts(candles, entries)
    if not mismatches:
        for stored, venue, instrument in entries:
            actual_hex, _ = _hash_series(
                candles,
                venue,
                instrument,
                stored.timeframe,
                stored.source,
                stored.start,
                stored.end,
                None,
            )
            if actual_hex != stored.series_hash:
                mismatches.append(
                    SeriesMismatch(
                        venue_symbol=stored.venue_symbol,
                        timeframe=stored.timeframe,
                        kind="hash",
                        expected=stored.series_hash,
                        actual=actual_hex,
                    )
                )
    return _report(dataset, mismatches, quality, audit)


def verify_series(
    candles: CandleRepository,
    datasets: DatasetRepository,
    resolve: SeriesResolver,
    quality: DataQualityEventRepository,
    audit: AuditEventWriter,
    dataset_name: str,
    version: str,
    venue_symbol: str,
    timeframe: Timeframe,
) -> VerifyReport:
    """Verify a single series of a dataset — what T7's replay calls to check
    only the series it is about to stream."""
    dataset, entries = _load(datasets, resolve, dataset_name, version)
    entries = [
        e for e in entries if e[0].venue_symbol == venue_symbol and e[0].timeframe == timeframe
    ]
    if not entries:
        raise DatasetError(
            f"series {venue_symbol} {timeframe.value} is not part of {dataset_name}@{version}"
        )
    mismatches = _check_counts(candles, entries)
    if not mismatches:
        stored, venue, instrument = entries[0]
        actual_hex, _ = _hash_series(
            candles,
            venue,
            instrument,
            stored.timeframe,
            stored.source,
            stored.start,
            stored.end,
            None,
        )
        if actual_hex != stored.series_hash:
            mismatches.append(
                SeriesMismatch(
                    venue_symbol=stored.venue_symbol,
                    timeframe=stored.timeframe,
                    kind="hash",
                    expected=stored.series_hash,
                    actual=actual_hex,
                )
            )
    return _report(dataset, mismatches, quality, audit, scope=f"{venue_symbol}/{timeframe.value}")


class SeriesResolver:
    """Resolves a stored series back to its (Venue, Instrument) in THIS
    database — instrument UUIDs are deliberately absent from dataset metadata
    (hash portability), so verification re-resolves by venue code + symbol."""

    def __init__(self, venues: VenueRepository, instruments: InstrumentRepository) -> None:
        self._venues = venues
        self._instruments = instruments

    def __call__(self, series: DatasetSeries) -> tuple[Venue, Instrument]:
        venue = self._venues.get_by_code(series.venue)
        if venue is None:
            raise DatasetError(f"venue {series.venue!r} not found — run `make seed`")
        instrument = self._instruments.get_by_venue_symbol(venue.venue_id, series.venue_symbol)
        if instrument is None:
            raise DatasetError(f"instrument {series.venue_symbol!r} not found on {series.venue}")
        return venue, instrument


def _load(
    datasets: DatasetRepository,
    resolve: SeriesResolver,
    dataset_name: str,
    version: str,
) -> tuple[Dataset, list[tuple[DatasetSeries, Venue, Instrument]]]:
    dataset = datasets.get(dataset_name, version)
    if dataset is None:
        raise DatasetError(f"dataset {dataset_name!r} version {version!r} not found")
    metadata = dataset.metadata or {}
    if metadata.get("canonical_version") != CANONICAL_VERSION:
        raise DatasetError(
            f"dataset uses serialization {metadata.get('canonical_version')!r}; "
            f"this code verifies {CANONICAL_VERSION!r} only"
        )
    entries = []
    for raw in metadata.get("series", []):
        stored = DatasetSeries.model_validate(raw)
        venue, instrument = resolve(stored)
        entries.append((stored, venue, instrument))
    if not entries:
        raise DatasetError(f"dataset {dataset_name}@{version} has no series metadata")
    return dataset, entries


def _check_counts(
    candles: CandleRepository,
    entries: list[tuple[DatasetSeries, Venue, Instrument]],
) -> list[SeriesMismatch]:
    mismatches = []
    for stored, _venue, instrument in entries:
        actual = candles.count_range(
            instrument.instrument_id, stored.timeframe, stored.source, stored.start, stored.end
        )
        if actual != stored.candle_count:
            mismatches.append(
                SeriesMismatch(
                    venue_symbol=stored.venue_symbol,
                    timeframe=stored.timeframe,
                    kind="count",
                    expected=str(stored.candle_count),
                    actual=str(actual),
                )
            )
    return mismatches


def _report(
    dataset: Dataset,
    mismatches: list[SeriesMismatch],
    quality: DataQualityEventRepository,
    audit: AuditEventWriter,
    scope: str = "full",
) -> VerifyReport:
    now = utc_now()
    total = int((dataset.metadata or {}).get("total_candles", 0))
    if mismatches:
        for mismatch in mismatches:
            quality.insert(
                DataQualityEvent(
                    event_id=new_id(),
                    dataset_type="datasets",
                    instrument_id=None,
                    severity=QualitySeverity.ERROR,
                    code=QualityCode.CANDLE_MISMATCH,
                    event_time=now,
                    details={
                        "dataset_name": dataset.dataset_name,
                        "version": dataset.version,
                        "venue_symbol": mismatch.venue_symbol,
                        "timeframe": mismatch.timeframe.value,
                        "kind": mismatch.kind,
                        "expected": mismatch.expected,
                        "actual": mismatch.actual,
                    },
                )
            )
        logger.error(
            "dataset_verify_failed",
            dataset=f"{dataset.dataset_name}@{dataset.version}",
            scope=scope,
            mismatches=len(mismatches),
        )
    audit.write(
        _event(
            "DATASET_VERIFY_FAILED" if mismatches else "DATASET_VERIFY_OK",
            dataset,
            AuditResult.FAILURE if mismatches else AuditResult.SUCCESS,
            {
                "dataset_name": dataset.dataset_name,
                "version": dataset.version,
                "scope": scope,
                "mismatches": [
                    f"{m.venue_symbol}/{m.timeframe.value}:{m.kind}" for m in mismatches
                ],
            },
        )
    )
    return VerifyReport(
        dataset_name=dataset.dataset_name,
        version=dataset.version,
        ok=not mismatches,
        candle_count=total,
        mismatches=mismatches,
    )


def _event(
    action: str,
    dataset: Dataset,
    result: AuditResult,
    metadata: dict[str, object],
) -> AuditEvent:
    return service_event(ACTOR_ID, action, "datasets", str(dataset.dataset_id), result, metadata)

"""Gap scan and backfill (T5, 03-Data-Engine §17-§20, Roadmap §26).

scan_gaps compares the stored series against the expected timeframe grid over
[start, end) and records one GAP quality event per hole. A hole already
covered by an unresolved GAP, or by a KNOWN_VENUE_GAP, is not re-recorded, so
rescanning is idempotent.

backfill_gaps refetches every unresolved GAP from the venue. Sub-ranges the
venue itself does not serve (maintenance windows, quarantined klines) are
recorded as KNOWN_VENUE_GAP — expected permanent holes that future scans
skip — and the GAP event is resolved once every missing candle is either
stored or reclassified. KNOWN_VENUE_GAP events are deliberately never
resolved: "unresolved" documents a hole that exists forever at the venue.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from quantlab.audit.events import AuditEvent, AuditResult, service_event
from quantlab.core.ids import new_id
from quantlab.core.logging import get_logger
from quantlab.core.timeutils import require_utc, utc_now
from quantlab.data.connector import HistoricalCandleSource
from quantlab.domain.models import (
    DataQualityEvent,
    Instrument,
    QualityCode,
    QualitySeverity,
    Timeframe,
)
from quantlab.storage.repositories import (
    AuditEventWriter,
    CandleRepository,
    DataQualityEventRepository,
)

logger = get_logger(__name__)

ACTOR_ID = "scan_gaps"


@dataclass(frozen=True)
class Hole:
    start: datetime
    end: datetime
    expected_candles: int
    already_known: bool


@dataclass(frozen=True)
class GapScanReport:
    venue_symbol: str
    timeframe: Timeframe
    start: datetime
    end: datetime
    holes: list[Hole]
    new_events: int

    @property
    def already_known(self) -> int:
        return len(self.holes) - self.new_events


@dataclass(frozen=True)
class BackfillReport:
    venue_symbol: str
    timeframe: Timeframe
    gaps_processed: int
    inserted: int
    filled: int
    known_venue_gaps: int


def align_up(ts: datetime, step: timedelta) -> datetime:
    """Smallest grid-aligned datetime >= ts (Binance grids are epoch-aligned)."""
    seconds = step.total_seconds()
    return datetime.fromtimestamp(math.ceil(ts.timestamp() / seconds) * seconds, tz=UTC)


def align_down(ts: datetime, step: timedelta) -> datetime:
    """Largest grid-aligned datetime <= ts."""
    seconds = step.total_seconds()
    return datetime.fromtimestamp(math.floor(ts.timestamp() / seconds) * seconds, tz=UTC)


def detect_holes(
    candles: CandleRepository,
    quality: DataQualityEventRepository,
    instrument: Instrument,
    timeframe: Timeframe,
    start: datetime,
    end: datetime,
    source_name: str,
) -> list[Hole]:
    """Report-only hole detection: missing ranges over [start, end) with
    their KNOWN_VENUE_GAP/unresolved-GAP coverage flag. Writes NOTHING —
    scan_gaps builds on this and records events; health reads it as is."""
    step = timeframe.duration
    start = align_up(require_utc(start, "start"), step)
    end = align_down(require_utc(end, "end"), step)
    if end <= start:
        raise ValueError("end must be strictly after start (after grid alignment)")
    missing = candles.missing_ranges(instrument.instrument_id, timeframe, source_name, start, end)
    covered = _covered_ranges(quality, instrument, timeframe, source_name)
    holes: list[Hole] = []
    for hole_start, hole_end in missing:
        known = any(c_start <= hole_start and hole_end <= c_end for c_start, c_end in covered)
        holes.append(Hole(hole_start, hole_end, int((hole_end - hole_start) / step), known))
    return holes


def scan_gaps(
    candles: CandleRepository,
    quality: DataQualityEventRepository,
    audit: AuditEventWriter,
    instrument: Instrument,
    timeframe: Timeframe,
    start: datetime,
    end: datetime,
    source_name: str,
) -> GapScanReport:
    """Detect missing candles over [start, end) and record new GAP events."""
    step = timeframe.duration
    start = align_up(require_utc(start, "start"), step)
    end = align_down(require_utc(end, "end"), step)
    holes = detect_holes(candles, quality, instrument, timeframe, start, end, source_name)

    now = utc_now()
    new_events = 0
    for hole in holes:
        if hole.already_known:
            continue
        hole_start, hole_end, expected = hole.start, hole.end, hole.expected_candles
        quality.insert(
            _quality_event(
                QualityCode.GAP,
                QualitySeverity.WARNING,
                instrument,
                timeframe,
                source_name,
                hole_start,
                hole_end,
                expected,
                now,
            )
        )
        new_events += 1
        logger.warning(
            "gap_detected",
            venue_symbol=instrument.venue_symbol,
            timeframe=timeframe.value,
            gap_start=hole_start.isoformat(),
            gap_end=hole_end.isoformat(),
            expected_candles=expected,
        )

    audit.write(
        _event(
            "GAP_SCAN_COMPLETED",
            instrument,
            AuditResult.SUCCESS,
            {
                "venue_symbol": instrument.venue_symbol,
                "timeframe": timeframe.value,
                "source": source_name,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "holes": len(holes),
                "new_events": new_events,
            },
        )
    )
    return GapScanReport(instrument.venue_symbol, timeframe, start, end, holes, new_events)


def backfill_gaps(
    source: HistoricalCandleSource,
    candles: CandleRepository,
    quality: DataQualityEventRepository,
    audit: AuditEventWriter,
    instrument: Instrument,
    timeframe: Timeframe,
    source_name: str,
    limit: int = 1000,
) -> BackfillReport:
    """Refetch every unresolved GAP; resolve it once filled or reclassified."""
    gaps = [
        event
        for event in quality.list_unresolved(instrument.instrument_id, QualityCode.GAP)
        if event.details is not None
        and event.details.get("timeframe") == timeframe.value
        and event.details.get("source") == source_name
    ]
    audit.write(
        _event(
            "GAP_BACKFILL_STARTED",
            instrument,
            AuditResult.SUCCESS,
            {
                "venue_symbol": instrument.venue_symbol,
                "timeframe": timeframe.value,
                "source": source_name,
                "gaps": len(gaps),
            },
        )
    )

    inserted = filled = known_venue = 0
    try:
        for event in gaps:
            assert event.details is not None  # filtered above
            gap_start = datetime.fromisoformat(event.details["gap_start"])
            gap_end = datetime.fromisoformat(event.details["gap_end"])
            inserted += _fill(source, candles, instrument, timeframe, gap_start, gap_end, limit)

            remaining = candles.missing_ranges(
                instrument.instrument_id, timeframe, source_name, gap_start, gap_end
            )
            now = utc_now()
            # Whatever the venue skipped in its own responses is a venue-side
            # hole: the fetch cursor only jumps a range when the venue returns
            # no (valid) kline for it. ponytail: a full page of quarantined
            # klines also lands here; if that ever occurs, expose raw coverage
            # from the source to tell the two cases apart.
            for hole_start, hole_end in remaining:
                quality.insert(
                    _quality_event(
                        QualityCode.KNOWN_VENUE_GAP,
                        QualitySeverity.INFO,
                        instrument,
                        timeframe,
                        source_name,
                        hole_start,
                        hole_end,
                        int((hole_end - hole_start) / timeframe.duration),
                        now,
                        reclassified_from=event.event_id,
                    )
                )
                known_venue += 1
                logger.info(
                    "known_venue_gap",
                    venue_symbol=instrument.venue_symbol,
                    timeframe=timeframe.value,
                    gap_start=hole_start.isoformat(),
                    gap_end=hole_end.isoformat(),
                )
            if not remaining:
                filled += 1
            quality.resolve(event.event_id, now)
    except Exception as exc:
        audit.write(
            _event(
                "GAP_BACKFILL_FAILED",
                instrument,
                AuditResult.FAILURE,
                {
                    "venue_symbol": instrument.venue_symbol,
                    "timeframe": timeframe.value,
                    "error": str(exc)[:500],
                    "inserted": inserted,
                },
            )
        )
        logger.error("backfill_failed", venue_symbol=instrument.venue_symbol, error=str(exc)[:200])
        raise

    audit.write(
        _event(
            "GAP_BACKFILL_COMPLETED",
            instrument,
            AuditResult.SUCCESS,
            {
                "venue_symbol": instrument.venue_symbol,
                "timeframe": timeframe.value,
                "source": source_name,
                "gaps": len(gaps),
                "inserted": inserted,
                "filled": filled,
                "known_venue_gaps": known_venue,
            },
        )
    )
    return BackfillReport(
        venue_symbol=instrument.venue_symbol,
        timeframe=timeframe,
        gaps_processed=len(gaps),
        inserted=inserted,
        filled=filled,
        known_venue_gaps=known_venue,
    )


def _fill(
    source: HistoricalCandleSource,
    candles: CandleRepository,
    instrument: Instrument,
    timeframe: Timeframe,
    gap_start: datetime,
    gap_end: datetime,
    limit: int,
) -> int:
    """Fetch [gap_start, gap_end) chunk by chunk; returns candles inserted.
    Unlike download_history there is no checkpoint: the cursor starts at the
    hole regardless of newer stored data."""
    inserted = 0
    cursor = gap_start
    while cursor < gap_end:
        batch = source.fetch_candles(instrument, timeframe, cursor, gap_end, limit)
        if not batch:
            break  # venue serves nothing (more) in this hole
        inserted += candles.insert_many(batch)
        next_cursor = batch[-1].open_time + timeframe.duration
        if next_cursor <= cursor:  # safety: a stuck cursor must never loop
            break
        cursor = next_cursor
    return inserted


def _covered_ranges(
    quality: DataQualityEventRepository,
    instrument: Instrument,
    timeframe: Timeframe,
    source_name: str,
) -> list[tuple[datetime, datetime]]:
    """[start, end) ranges already tracked by an unresolved GAP or a
    KNOWN_VENUE_GAP for this series."""
    ranges: list[tuple[datetime, datetime]] = []
    for code in (QualityCode.GAP, QualityCode.KNOWN_VENUE_GAP):
        for event in quality.list_unresolved(instrument.instrument_id, code):
            details = event.details or {}
            if details.get("timeframe") != timeframe.value:
                continue
            if details.get("source") != source_name:
                continue
            ranges.append(
                (
                    datetime.fromisoformat(details["gap_start"]),
                    datetime.fromisoformat(details["gap_end"]),
                )
            )
    return ranges


def _quality_event(
    code: QualityCode,
    severity: QualitySeverity,
    instrument: Instrument,
    timeframe: Timeframe,
    source_name: str,
    gap_start: datetime,
    gap_end: datetime,
    expected: int,
    now: datetime,
    reclassified_from: object | None = None,
) -> DataQualityEvent:
    details: dict[str, object] = {
        "venue_symbol": instrument.venue_symbol,
        "timeframe": timeframe.value,
        "source": source_name,
        "gap_start": gap_start.isoformat(),
        "gap_end": gap_end.isoformat(),
        "expected_candles": expected,
    }
    if reclassified_from is not None:
        details["reclassified_from"] = str(reclassified_from)
    return DataQualityEvent(
        event_id=new_id(),
        dataset_type="candles",
        instrument_id=instrument.instrument_id,
        severity=severity,
        code=code,
        event_time=now,
        details=details,
    )


def _event(
    action: str,
    instrument: Instrument,
    result: AuditResult,
    metadata: dict[str, object],
) -> AuditEvent:
    resource_id = str(instrument.instrument_id)
    return service_event(ACTOR_ID, action, "candles", resource_id, result, metadata)

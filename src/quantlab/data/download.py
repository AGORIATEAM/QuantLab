"""Resumable historical candle download (03-Data-Engine §14, Roadmap §24).

Resume is derived from the data itself: the checkpoint is the newest stored
open_time for (instrument, timeframe, source). Combined with the idempotent
batch insert (unique constraint + ON CONFLICT DO NOTHING), the download is
restartable after any interruption and a rerun over a covered range inserts
nothing. Interior gaps (venue holes or partial failures) are the gap scan's
job (T5), not the cursor's.

Degenerate edge: if a fetched page ends in nothing but quarantined klines,
the cursor stops at the last valid candle and the run ends there; the gap
scan surfaces the remainder.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from quantlab.audit.events import ActorType, AuditEvent, AuditResult
from quantlab.core.ids import new_id
from quantlab.core.logging import get_logger
from quantlab.core.timeutils import require_utc
from quantlab.data.connector import HistoricalCandleSource
from quantlab.domain.models import Instrument, Timeframe
from quantlab.storage.repositories import AuditEventWriter, CandleRepository

logger = get_logger(__name__)

ACTOR_ID = "download_history"


@dataclass(frozen=True)
class DownloadReport:
    venue_symbol: str
    timeframe: Timeframe
    start: datetime
    end: datetime
    resumed_from: datetime | None
    batches: int
    fetched: int
    inserted: int

    @property
    def duplicates_skipped(self) -> int:
        return self.fetched - self.inserted


def download_history(
    source: HistoricalCandleSource,
    candles: CandleRepository,
    audit: AuditEventWriter,
    instrument: Instrument,
    timeframe: Timeframe,
    start: datetime,
    end: datetime,
    source_name: str,
    limit: int = 1000,
) -> DownloadReport:
    """Download [start, end) into storage, batch by batch, resuming from the
    newest stored candle. Journaled via audit events and structured logs."""
    start = require_utc(start, "start")
    end = require_utc(end, "end")
    if end <= start:
        raise ValueError("end must be strictly after start")

    checkpoint = candles.latest_open_time(instrument.instrument_id, timeframe, source_name)
    cursor = start if checkpoint is None else max(start, checkpoint + timeframe.duration)

    audit.write(
        _event(
            "HISTORICAL_DOWNLOAD_STARTED",
            instrument,
            AuditResult.SUCCESS,
            {
                "venue_symbol": instrument.venue_symbol,
                "timeframe": timeframe.value,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "resumed_from": None if checkpoint is None else checkpoint.isoformat(),
                "source": source_name,
            },
        )
    )
    logger.info(
        "download_started",
        venue_symbol=instrument.venue_symbol,
        timeframe=timeframe.value,
        start=start.isoformat(),
        end=end.isoformat(),
        resumed_from=None if checkpoint is None else checkpoint.isoformat(),
    )

    batches = fetched = inserted = 0
    try:
        while cursor < end:
            batch = source.fetch_candles(instrument, timeframe, cursor, end, limit)
            if not batch:
                break  # venue has no (more) data in the remaining range
            batches += 1
            fetched += len(batch)
            inserted += candles.insert_many(batch)
            logger.info(
                "download_chunk",
                venue_symbol=instrument.venue_symbol,
                timeframe=timeframe.value,
                chunk_start=batch[0].open_time.isoformat(),
                chunk_size=len(batch),
                inserted_total=inserted,
            )
            cursor = batch[-1].open_time + timeframe.duration
    except Exception as exc:
        audit.write(
            _event(
                "HISTORICAL_DOWNLOAD_FAILED",
                instrument,
                AuditResult.FAILURE,
                {
                    "venue_symbol": instrument.venue_symbol,
                    "timeframe": timeframe.value,
                    "error": str(exc)[:500],
                    "batches": batches,
                    "inserted": inserted,
                },
            )
        )
        logger.error("download_failed", venue_symbol=instrument.venue_symbol, error=str(exc)[:200])
        raise

    audit.write(
        _event(
            "HISTORICAL_DOWNLOAD_COMPLETED",
            instrument,
            AuditResult.SUCCESS,
            {
                "venue_symbol": instrument.venue_symbol,
                "timeframe": timeframe.value,
                "batches": batches,
                "fetched": fetched,
                "inserted": inserted,
                "duplicates_skipped": fetched - inserted,
            },
        )
    )
    return DownloadReport(
        venue_symbol=instrument.venue_symbol,
        timeframe=timeframe,
        start=start,
        end=end,
        resumed_from=checkpoint,
        batches=batches,
        fetched=fetched,
        inserted=inserted,
    )


def _event(
    action: str,
    instrument: Instrument,
    result: AuditResult,
    metadata: dict[str, object],
) -> AuditEvent:
    return AuditEvent(
        audit_event_id=new_id(),
        actor_type=ActorType.SERVICE,
        actor_id=ACTOR_ID,
        action=action,
        resource_type="candles",
        resource_id=str(instrument.instrument_id),
        environment=None,
        request_id=None,
        correlation_id=None,
        result=result,
        metadata=metadata,
    )

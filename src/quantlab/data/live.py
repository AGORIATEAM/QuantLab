"""Live WebSocket ingestion (T8, ADR-0001 addendum A, docs/03 §15-§16).

Pipeline per closed kline message: archive the raw frame (append-only
journal, no deduplication — A.2), parse to RawKline, then the SAME
normalize→validate path as REST (T3), insert with source='binance_ws'
(idempotent). Intra-candle updates (x=false) are ignored and not archived.

Reconnection: bounded backoff. At every (re)connection, for each series with
prior WS data, the hole since the last WS candle is recorded as a WS_OUTAGE
quality event (operational reliability measure) and the missed candles are
fetched over REST into their TRUE provenance, source='binance' (A.3) — the
binance_ws series keeps its hole; live consumers read the candles_canonical
view (A.4). The first connection starts the WS series at "now": history is
REST's job.

Latency is measured per message: venue event time → reception → insertion
(docs/03 §33) and logged; full staleness detection is T9's scope.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import datetime

from quantlab.audit.events import AuditEvent, AuditResult, service_event
from quantlab.core.clock import Clock, WallClock
from quantlab.core.ids import new_id
from quantlab.core.logging import get_logger
from quantlab.data.binance.ws import WsKlineEvent, parse_ws_message
from quantlab.data.connector import HistoricalCandleSource
from quantlab.data.download import download_history
from quantlab.data.errors import MalformedPayloadError
from quantlab.data.gaps import align_down
from quantlab.data.validate import normalize_and_validate
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
    RawWsMessageWriter,
)

logger = get_logger(__name__)

ACTOR_ID = "live_ingest"
SOURCE_BINANCE_WS = "binance_ws"
SOURCE_BINANCE_REST = "binance"


@dataclass
class LiveStats:
    """Running counters, readable by the caller at any time."""

    messages: int = 0
    closed_klines: int = 0
    archived: int = 0
    inserted: int = 0
    duplicates: int = 0
    malformed: int = 0
    reconciled: int = 0
    outages: int = 0
    last_latency_ms: float | None = None


class LiveIngestor:
    """Processes parsed WS frames for a fixed set of (instrument, timeframe)
    series. One instance per connection lifetime or across reconnects."""

    def __init__(
        self,
        candles: CandleRepository,
        quality: DataQualityEventRepository,
        raw_messages: RawWsMessageWriter,
        instruments: dict[str, Instrument],
        timeframes: list[Timeframe],
        clock: Clock | None = None,
    ) -> None:
        self._candles = candles
        self._quality = quality
        self._raw = raw_messages
        self._instruments = instruments
        self._timeframes = timeframes
        self._clock = clock if clock is not None else WallClock()
        self.stats = LiveStats()

    def process_frame(self, text: str) -> None:
        self.stats.messages += 1
        received_at = self._clock.now()
        try:
            event = parse_ws_message(text)
        except MalformedPayloadError as exc:
            self.stats.malformed += 1
            logger.warning("ws_malformed_frame", error=str(exc)[:200])
            return
        if event is None or not event.closed:
            return  # non-kline frame or intra-candle update: not archived (A.1)
        self._ingest_closed(event, received_at)

    def _ingest_closed(self, event: WsKlineEvent, received_at: datetime) -> None:
        self.stats.closed_klines += 1
        instrument = self._instruments.get(event.venue_symbol)
        if instrument is None:
            logger.warning("ws_unknown_symbol", venue_symbol=event.venue_symbol)
            return
        # 1. raw journal first (A.2): everything the venue pushed, as pushed
        self._raw.insert(new_id(), received_at, event.stream, event.payload)
        self.stats.archived += 1
        # 2. same normalize→validate path as REST (T3), quarantine included
        candles = normalize_and_validate(
            [event.kline],
            instrument,
            event.timeframe,
            SOURCE_BINANCE_WS,
            self._quality,
            now=received_at,
        )
        inserted = self._candles.insert_many(candles)
        self.stats.inserted += inserted
        self.stats.duplicates += len(candles) - inserted
        latency_ms = (received_at.timestamp() * 1000) - event.event_time_ms
        self.stats.last_latency_ms = latency_ms
        logger.info(
            "ws_candle_ingested",
            venue_symbol=event.venue_symbol,
            timeframe=event.timeframe.value,
            open_time_ms=event.kline.open_time_ms,
            inserted=inserted,
            latency_ms=round(latency_ms, 1),
        )

    def reconcile(self, rest_source: HistoricalCandleSource, audit: AuditEventWriter) -> None:
        """On (re)connection: record the WS hole per series (WS_OUTAGE) and
        fetch the missed candles over REST into source='binance' (A.3).
        A series with no prior WS data simply starts now."""
        now = self._clock.now()
        for instrument in self._instruments.values():
            for timeframe in self._timeframes:
                checkpoint = self._candles.latest_open_time(
                    instrument.instrument_id, timeframe, SOURCE_BINANCE_WS
                )
                if checkpoint is None:
                    continue
                gap_start = checkpoint + timeframe.duration
                gap_end = align_down(now, timeframe.duration)
                expected = int((gap_end - gap_start) / timeframe.duration)
                if expected <= 0:
                    continue
                self.stats.outages += 1
                self._quality.insert(
                    DataQualityEvent(
                        event_id=new_id(),
                        dataset_type="candles",
                        instrument_id=instrument.instrument_id,
                        severity=QualitySeverity.WARNING,
                        code=QualityCode.WS_OUTAGE,
                        event_time=now,
                        details={
                            "venue_symbol": instrument.venue_symbol,
                            "timeframe": timeframe.value,
                            "source": SOURCE_BINANCE_WS,
                            "gap_start": gap_start.isoformat(),
                            "gap_end": gap_end.isoformat(),
                            "expected_candles": expected,
                        },
                    )
                )
                report = download_history(
                    rest_source,
                    self._candles,
                    audit,
                    instrument,
                    timeframe,
                    gap_start,
                    gap_end,
                    SOURCE_BINANCE_REST,
                )
                self.stats.reconciled += report.inserted
                logger.warning(
                    "ws_outage_reconciled",
                    venue_symbol=instrument.venue_symbol,
                    timeframe=timeframe.value,
                    gap_start=gap_start.isoformat(),
                    gap_end=gap_end.isoformat(),
                    missed=expected,
                    rest_inserted=report.inserted,
                )


def run_live_ingestion(
    frames_factory: Callable[[], Iterator[str]],
    ingestor: LiveIngestor,
    rest_source: HistoricalCandleSource,
    audit: AuditEventWriter,
    should_stop: Callable[[], bool],
    max_backoff_seconds: float = 60.0,
) -> LiveStats:
    """Connection loop: reconcile, consume frames, reconnect with bounded
    backoff on any error (a stream that ends counts as a disconnect), until
    should_stop() is true. frames_factory() returns a fresh frame iterator
    per connection attempt."""
    audit.write(_event("LIVE_INGEST_STARTED", AuditResult.SUCCESS, {}))
    backoff = 1.0
    try:
        while not should_stop():
            try:
                ingestor.reconcile(rest_source, audit)
                for frame in frames_factory():
                    ingestor.process_frame(frame)
                    backoff = 1.0
                    if should_stop():
                        return ingestor.stats
                logger.warning("ws_stream_ended")
            except Exception as exc:
                if should_stop():
                    break
                logger.warning("ws_disconnected", error=str(exc)[:200], retry_in_seconds=backoff)
            time.sleep(backoff)
            backoff = min(backoff * 2, max_backoff_seconds)
    finally:
        stats = ingestor.stats
        audit.write(
            _event(
                "LIVE_INGEST_STOPPED",
                AuditResult.SUCCESS,
                {
                    "messages": stats.messages,
                    "closed_klines": stats.closed_klines,
                    "archived": stats.archived,
                    "inserted": stats.inserted,
                    "duplicates": stats.duplicates,
                    "malformed": stats.malformed,
                    "reconciled": stats.reconciled,
                    "outages": stats.outages,
                },
            )
        )
    return ingestor.stats


def _event(action: str, result: AuditResult, metadata: dict[str, object]) -> AuditEvent:
    return service_event(ACTOR_ID, action, "candles", None, result, metadata)

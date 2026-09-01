"""Data health check (T9, roadmap §33 — strict Phase 1 scope: a command,
not a dashboard; the full Monitoring Engine is docs/13, a later phase).

Per series: freshness of the REST and WS sources (age of the last candle
against per-timeframe thresholds) and completeness of the REST series
(report-only hole detection via gaps.detect_holes — nothing is written;
WS holes are already tracked as WS_OUTAGE events, aggregated here instead).
Globally: open quality events by code (KNOWN_VENUE_GAP listed apart, open by
design, never blocking), WS_OUTAGE frequency/duration over a window, and WS
ingestion latency (avg/p95/max) computed in SQL from the raw journal.

Verdict: healthy unless a REST series is stale or has unexplained holes.
WS freshness (stale or never seen) is measured and reported but
INFORMATIONAL by default: live ingestion is not (yet) expected to run
continuously, so a stopped or never-started WS feed must not fail the
daily sync. Pass require_ws once live runs as a daemon to make WS
freshness blocking.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from quantlab.audit.events import AuditResult, service_event
from quantlab.core.clock import Clock, WallClock
from quantlab.core.logging import get_logger
from quantlab.data.gaps import Hole, detect_holes
from quantlab.domain.models import Instrument, QualityCode, Timeframe
from quantlab.storage.repositories import (
    AuditEventWriter,
    CandleRepository,
    DataQualityEventRepository,
    RawWsMessageWriter,
)

logger = get_logger(__name__)

ACTOR_ID = "health_check"
DATA_EPOCH = datetime(2017, 8, 17, tzinfo=UTC)  # start of the certified store
SOURCE_REST = "binance"
SOURCE_WS = "binance_ws"


@dataclass(frozen=True)
class SourceFreshness:
    age_seconds: float | None  # None = never seen
    threshold_seconds: float
    stale: bool

    @property
    def never_seen(self) -> bool:
        return self.age_seconds is None


@dataclass(frozen=True)
class SeriesHealth:
    venue_symbol: str
    timeframe: Timeframe
    rest: SourceFreshness
    ws: SourceFreshness
    ws_blocking: bool  # require_ws: WS freshness counts toward the verdict
    unexplained_holes: int
    missing_candles: int

    @property
    def healthy(self) -> bool:
        if self.rest.stale or self.unexplained_holes:
            return False
        if self.ws_blocking and (self.ws.stale or self.ws.never_seen):
            return False
        return True


@dataclass(frozen=True)
class OutageSummary:
    count: int
    missed_candles: int
    total_duration_seconds: float

    @property
    def avg_duration_seconds(self) -> float:
        return self.total_duration_seconds / self.count if self.count else 0.0


@dataclass
class HealthReport:
    series: list[SeriesHealth] = field(default_factory=list)
    open_events: dict[str, int] = field(default_factory=dict)  # sans KNOWN_VENUE_GAP
    known_venue_gaps: int = 0
    ws_outages: OutageSummary = field(default_factory=lambda: OutageSummary(0, 0, 0.0))
    ws_latency: tuple[float, float, float, int] | None = None  # avg, p95, max ms, count

    @property
    def healthy(self) -> bool:
        return all(s.healthy for s in self.series)


def check_health(
    candles: CandleRepository,
    quality: DataQualityEventRepository,
    raw_messages: RawWsMessageWriter,
    audit: AuditEventWriter,
    instruments: list[Instrument],
    timeframes: list[Timeframe],
    clock: Clock | None = None,
    ws_grace_multiplier: float = 3.0,
    rest_grace: timedelta = timedelta(hours=25),
    outages_since: timedelta = timedelta(days=7),
    latency_since: timedelta = timedelta(hours=24),
    require_ws: bool = False,
) -> HealthReport:
    """Build the health report and journal a HEALTH_CHECK audit event whose
    result mirrors the verdict."""
    now = (clock or WallClock()).now()
    report = HealthReport()

    for instrument in instruments:
        for timeframe in timeframes:
            duration = timeframe.duration
            rest = _freshness(
                candles,
                instrument,
                timeframe,
                SOURCE_REST,
                now,
                threshold=rest_grace + duration,
                blocking_when_never_seen=True,
            )
            ws = _freshness(
                candles,
                instrument,
                timeframe,
                SOURCE_WS,
                now,
                threshold=duration * ws_grace_multiplier,
                blocking_when_never_seen=require_ws,
            )
            holes = _rest_holes(candles, quality, instrument, timeframe, now)
            unexplained = [h for h in holes if not h.already_known]
            report.series.append(
                SeriesHealth(
                    venue_symbol=instrument.venue_symbol,
                    timeframe=timeframe,
                    rest=rest,
                    ws=ws,
                    ws_blocking=require_ws,
                    unexplained_holes=len(unexplained),
                    missing_candles=sum(h.expected_candles for h in unexplained),
                )
            )

    _collect_events(quality, report, now - outages_since)
    report.ws_latency = raw_messages.latency_stats(now - latency_since)

    audit.write(
        service_event(
            ACTOR_ID,
            "HEALTH_CHECK",
            "candles",
            None,
            AuditResult.SUCCESS if report.healthy else AuditResult.FAILURE,
            {
                "healthy": report.healthy,
                "series": len(report.series),
                "stale": [
                    f"{s.venue_symbol}/{s.timeframe.value}" for s in report.series if not s.healthy
                ],
                "unexplained_holes": sum(s.unexplained_holes for s in report.series),
                "open_events": report.open_events,
                "ws_outages": report.ws_outages.count,
            },
        )
    )
    return report


def _freshness(
    candles: CandleRepository,
    instrument: Instrument,
    timeframe: Timeframe,
    source: str,
    now: datetime,
    threshold: timedelta,
    blocking_when_never_seen: bool,
) -> SourceFreshness:
    latest = candles.latest_open_time(instrument.instrument_id, timeframe, source)
    if latest is None:
        return SourceFreshness(None, threshold.total_seconds(), stale=blocking_when_never_seen)
    age = (now - (latest + timeframe.duration)).total_seconds()
    return SourceFreshness(age, threshold.total_seconds(), stale=age > threshold.total_seconds())


def _rest_holes(
    candles: CandleRepository,
    quality: DataQualityEventRepository,
    instrument: Instrument,
    timeframe: Timeframe,
    now: datetime,
) -> list[Hole]:
    latest = candles.latest_open_time(instrument.instrument_id, timeframe, SOURCE_REST)
    if latest is None:
        return []
    end = latest + timeframe.duration  # trailing freshness is the staleness check's job
    if end <= DATA_EPOCH:
        return []
    return detect_holes(candles, quality, instrument, timeframe, DATA_EPOCH, end, SOURCE_REST)


def _collect_events(
    quality: DataQualityEventRepository, report: HealthReport, outages_since: datetime
) -> None:
    count = 0
    missed = 0
    duration = 0.0
    for event in quality.list_unresolved():
        code = event.code.value
        if event.code is QualityCode.KNOWN_VENUE_GAP:
            report.known_venue_gaps += 1
            continue
        report.open_events[code] = report.open_events.get(code, 0) + 1
        if event.code is QualityCode.WS_OUTAGE and event.event_time >= outages_since:
            details = event.details or {}
            count += 1
            missed += int(details.get("expected_candles", 0))
            try:
                gap_start = datetime.fromisoformat(str(details["gap_start"]))
                gap_end = datetime.fromisoformat(str(details["gap_end"]))
                duration += (gap_end - gap_start).total_seconds()
            except (KeyError, ValueError):
                pass
    report.ws_outages = OutageSummary(count, missed, duration)


def format_report(report: HealthReport) -> str:
    """Human-readable table + summary."""
    lines = [
        f"{'series':<14}{'rest age':>12}{'rest':>7}{'ws age':>12}{'ws':>11}"
        f"{'holes':>7}{'missing':>9}"
    ]
    for s in report.series:
        rest_age = _fmt_age(s.rest.age_seconds)
        ws_age = _fmt_age(s.ws.age_seconds)
        ws_state = "never" if s.ws.never_seen else ("STALE" if s.ws.stale else "ok")
        rest_state = "STALE" if s.rest.stale else "ok"
        lines.append(
            f"{s.venue_symbol + '/' + s.timeframe.value:<14}{rest_age:>12}{rest_state:>7}"
            f"{ws_age:>12}{ws_state:>11}{s.unexplained_holes:>7}{s.missing_candles:>9}"
        )
    lines.append("")
    events = ", ".join(f"{k}={v}" for k, v in sorted(report.open_events.items())) or "none"
    lines.append(f"open quality events: {events}")
    lines.append(f"known venue gaps (open by design): {report.known_venue_gaps}")
    o = report.ws_outages
    lines.append(
        f"ws outages (window): {o.count}, missed candles: {o.missed_candles}, "
        f"total downtime: {o.total_duration_seconds:.0f}s, avg: {o.avg_duration_seconds:.0f}s"
    )
    if report.ws_latency:
        avg, p95, mx, n = report.ws_latency
        lines.append(
            f"ws latency (24h, {n} msgs): avg {avg:.0f}ms, p95 {p95:.0f}ms, max {mx:.0f}ms"
        )
    else:
        lines.append("ws latency (24h): no messages")
    if report.series and not report.series[0].ws_blocking:
        lines.append("ws freshness is informational (pass --require-ws to enforce it)")
    lines.append(f"verdict: {'HEALTHY' if report.healthy else 'UNHEALTHY'}")
    return "\n".join(lines)


def _fmt_age(seconds: float | None) -> str:
    if seconds is None:
        return "-"
    if seconds < 90:
        return f"{seconds:.0f}s"
    if seconds < 5400:
        return f"{seconds / 60:.0f}m"
    if seconds < 90000:
        return f"{seconds / 3600:.1f}h"
    return f"{seconds / 86400:.1f}d"

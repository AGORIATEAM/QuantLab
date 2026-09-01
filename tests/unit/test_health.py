"""Health check: freshness verdicts, unexplained-hole counting, outage
aggregation, never-seen WS handling, report-only guarantee."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fakes import InMemoryCandles, InMemoryQualityEvents, InMemoryRawWsMessages, RecordingAudit

from quantlab.audit.events import AuditResult
from quantlab.core.clock import SimulatedClock
from quantlab.core.ids import new_id
from quantlab.data.gaps import detect_holes
from quantlab.data.health import (
    DATA_EPOCH,
    HealthReport,
    SeriesHealth,
    SourceFreshness,
    check_health,
)
from quantlab.domain.models import (
    Candle,
    DataQualityEvent,
    Instrument,
    QualityCode,
    QualitySeverity,
    Timeframe,
)

TF = Timeframe.H1
NOW = datetime(2026, 9, 2, 12, 0, tzinfo=UTC)

BTC = Instrument(
    instrument_id=new_id(),
    venue_id=new_id(),
    asset_id=None,
    venue_symbol="BTCUSDT",
    instrument_type="spot",
    tick_size=Decimal("0.01"),
    lot_size=Decimal("0.00001"),
)


def make_candle(open_time: datetime, source: str = "binance") -> Candle:
    return Candle(
        candle_id=new_id(),
        instrument_id=BTC.instrument_id,
        timeframe=TF,
        open_time=open_time,
        close_time=open_time + TF.duration,
        open=Decimal("100"),
        high=Decimal("101"),
        low=Decimal("99"),
        close=Decimal("100.5"),
        volume=Decimal("1"),
        source=source,
    )


def hours_ago(n: float) -> datetime:
    return NOW - timedelta(hours=n)


def run_check(
    candles: InMemoryCandles,
    quality: InMemoryQualityEvents | None = None,
    **kwargs: object,
) -> tuple[HealthReport, InMemoryQualityEvents, RecordingAudit]:
    quality = quality or InMemoryQualityEvents()
    audit = RecordingAudit()
    report = check_health(
        candles,
        quality,
        InMemoryRawWsMessages(),
        audit,
        [BTC],
        [TF],
        clock=SimulatedClock(NOW),
        **kwargs,
    )
    return report, quality, audit


def test_fresh_and_complete_series_is_healthy() -> None:
    candles = InMemoryCandles()
    rows = [make_candle(DATA_EPOCH + i * TF.duration) for i in range(5)]
    candles.insert_many(rows)
    # freshness measured against a clock just after the last close
    clock_now = DATA_EPOCH + 5 * TF.duration + timedelta(minutes=10)
    report = check_health(
        candles,
        InMemoryQualityEvents(),
        InMemoryRawWsMessages(),
        RecordingAudit(),
        [BTC],
        [TF],
        clock=SimulatedClock(clock_now),
    )
    series = report.series[0]
    assert not series.rest.stale
    assert series.unexplained_holes == 0
    assert series.ws.never_seen and not series.ws.stale  # non-blocking by default
    assert report.healthy


def test_stale_rest_fails_verdict_and_audit_reports_failure() -> None:
    candles = InMemoryCandles()
    candles.insert_many([make_candle(hours_ago(40))])  # last close 39h ago > 25h+1h
    # (the lone candle also creates a huge leading hole — both signals fire)
    report, _quality, audit = run_check(candles)
    assert report.series[0].rest.stale
    assert not report.healthy
    assert audit.events[-1].action == "HEALTH_CHECK"
    assert audit.events[-1].result is AuditResult.FAILURE


def test_unexplained_hole_blocks_and_covered_hole_does_not() -> None:
    candles = InMemoryCandles()
    # epoch..+2h stored, +2h..+3h missing, +3h..+4h stored — one interior hole
    rows = [make_candle(DATA_EPOCH + i * TF.duration) for i in (0, 1, 3)]
    candles.insert_many(rows)
    clock_now = DATA_EPOCH + 4 * TF.duration + timedelta(minutes=5)
    quality = InMemoryQualityEvents()

    def check() -> tuple[bool, int]:
        report = check_health(
            candles,
            quality,
            InMemoryRawWsMessages(),
            RecordingAudit(),
            [BTC],
            [TF],
            clock=SimulatedClock(clock_now),
        )
        s = report.series[0]
        return report.healthy, s.unexplained_holes

    healthy, holes = check()
    assert not healthy and holes == 1

    # cover the hole with a KNOWN_VENUE_GAP -> no longer unexplained
    quality.insert(
        DataQualityEvent(
            event_id=new_id(),
            dataset_type="candles",
            instrument_id=BTC.instrument_id,
            severity=QualitySeverity.INFO,
            code=QualityCode.KNOWN_VENUE_GAP,
            event_time=clock_now,
            details={
                "timeframe": TF.value,
                "source": "binance",
                "gap_start": (DATA_EPOCH + 2 * TF.duration).isoformat(),
                "gap_end": (DATA_EPOCH + 3 * TF.duration).isoformat(),
            },
        )
    )
    healthy, holes = check()
    assert healthy and holes == 0


def test_require_ws_makes_never_seen_blocking() -> None:
    candles = InMemoryCandles()
    candles.insert_many([make_candle(DATA_EPOCH)])
    clock_now = DATA_EPOCH + TF.duration + timedelta(minutes=1)
    report = check_health(
        candles,
        InMemoryQualityEvents(),
        InMemoryRawWsMessages(),
        RecordingAudit(),
        [BTC],
        [TF],
        clock=SimulatedClock(clock_now),
        require_ws=True,
    )
    assert report.series[0].ws.never_seen
    assert not report.healthy


def test_ws_freshness_uses_grace_multiplier() -> None:
    candles = InMemoryCandles()
    candles.insert_many([make_candle(DATA_EPOCH)])
    candles.insert_many([make_candle(hours_ago(5), source="binance_ws")])
    # ws last close 4h ago; threshold 3x1h => stale
    report, _q, _a = run_check(candles)
    assert report.series[0].ws.stale  # measured: 4h age > 3x1h
    candles.insert_many([make_candle(hours_ago(2), source="binance_ws")])
    report, _q, _a = run_check(candles)
    assert not report.series[0].ws.stale  # 1h age <= 3h


def test_ws_staleness_is_informational_unless_blocking() -> None:
    fresh_rest = SourceFreshness(age_seconds=60.0, threshold_seconds=90000.0, stale=False)
    stale_ws = SourceFreshness(age_seconds=14400.0, threshold_seconds=10800.0, stale=True)

    def series(ws_blocking: bool) -> SeriesHealth:
        return SeriesHealth(
            venue_symbol="BTCUSDT",
            timeframe=TF,
            rest=fresh_rest,
            ws=stale_ws,
            ws_blocking=ws_blocking,
            unexplained_holes=0,
            missing_candles=0,
        )

    assert series(ws_blocking=False).healthy  # a stopped live feed does not fail sync
    assert not series(ws_blocking=True).healthy  # --require-ws enforces it


def test_outage_aggregation_windowed_and_known_gaps_apart() -> None:
    candles = InMemoryCandles()
    candles.insert_many([make_candle(DATA_EPOCH)])
    quality = InMemoryQualityEvents()

    def outage(when: datetime, missed: int, minutes: int) -> DataQualityEvent:
        return DataQualityEvent(
            event_id=new_id(),
            dataset_type="candles",
            instrument_id=BTC.instrument_id,
            severity=QualitySeverity.WARNING,
            code=QualityCode.WS_OUTAGE,
            event_time=when,
            details={
                "expected_candles": missed,
                "gap_start": when.isoformat(),
                "gap_end": (when + timedelta(minutes=minutes)).isoformat(),
            },
        )

    quality.insert(outage(NOW - timedelta(days=1), missed=2, minutes=2))
    quality.insert(outage(NOW - timedelta(days=2), missed=4, minutes=6))
    quality.insert(outage(NOW - timedelta(days=30), missed=99, minutes=99))  # out of window

    report, _q, _a = run_check(candles, quality=quality)
    assert report.ws_outages.count == 2
    assert report.ws_outages.missed_candles == 6
    assert report.ws_outages.total_duration_seconds == 8 * 60
    assert report.open_events["WS_OUTAGE"] == 3  # all open events still counted by code
    assert report.known_venue_gaps == 0


def test_detect_holes_writes_nothing() -> None:
    candles = InMemoryCandles()
    candles.insert_many([make_candle(DATA_EPOCH), make_candle(DATA_EPOCH + 2 * TF.duration)])
    quality = InMemoryQualityEvents()
    holes = detect_holes(
        candles, quality, BTC, TF, DATA_EPOCH, DATA_EPOCH + 3 * TF.duration, "binance"
    )
    assert [(h.expected_candles, h.already_known) for h in holes] == [(1, False)]
    assert quality.events == []  # report-only: no GAP event was recorded

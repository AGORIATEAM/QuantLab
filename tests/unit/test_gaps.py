"""scan_gaps / backfill_gaps: detection, idempotent rescans, reclassification."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fakes import GridSource, InMemoryCandles, InMemoryQualityEvents, RecordingAudit

from quantlab.core.ids import new_id
from quantlab.data.gaps import GapScanReport, backfill_gaps, scan_gaps
from quantlab.domain.models import Candle, Instrument, QualityCode, QualitySeverity, Timeframe

TF = Timeframe.H1
T0 = datetime(2026, 8, 1, 0, 0, tzinfo=UTC)
SOURCE = "binance"

INSTRUMENT = Instrument(
    instrument_id=new_id(),
    venue_id=new_id(),
    asset_id=None,
    venue_symbol="BTCUSDT",
    instrument_type="spot",
    tick_size=Decimal("0.01"),
    lot_size=Decimal("0.00001"),
)


def make_candle(open_time: datetime) -> Candle:
    return Candle(
        candle_id=new_id(),
        instrument_id=INSTRUMENT.instrument_id,
        timeframe=TF,
        open_time=open_time,
        close_time=open_time + TF.duration,
        open=Decimal("100"),
        high=Decimal("101"),
        low=Decimal("99"),
        close=Decimal("100.5"),
        volume=Decimal("1"),
        source=SOURCE,
    )


def hour(i: int) -> datetime:
    return T0 + i * TF.duration


def harness(
    stored_hours: list[int],
) -> tuple[InMemoryCandles, InMemoryQualityEvents, RecordingAudit]:
    repo = InMemoryCandles()
    repo.insert_many([make_candle(hour(i)) for i in stored_hours])
    return repo, InMemoryQualityEvents(), RecordingAudit()


def scan(
    repo: InMemoryCandles,
    quality: InMemoryQualityEvents,
    audit: RecordingAudit,
    start: datetime = T0,
    end: datetime | None = None,
) -> GapScanReport:
    return scan_gaps(repo, quality, audit, INSTRUMENT, TF, start, end or hour(10), SOURCE)


def test_detects_leading_interior_and_trailing_holes() -> None:
    repo, quality, audit = harness([2, 3, 6, 8])  # holes: [0,2) [4,6) [7,8) [9,10)
    report = scan(repo, quality, audit)

    assert [(h.start, h.end, h.expected_candles) for h in report.holes] == [
        (hour(0), hour(2), 2),
        (hour(4), hour(6), 2),
        (hour(7), hour(8), 1),
        (hour(9), hour(10), 1),
    ]
    assert report.new_events == 4
    events = quality.list_unresolved(INSTRUMENT.instrument_id, QualityCode.GAP)
    assert len(events) == 4
    assert all(e.severity is QualitySeverity.WARNING for e in events)
    assert audit.events[-1].action == "GAP_SCAN_COMPLETED"


def test_empty_series_is_one_big_hole() -> None:
    repo, quality, audit = harness([])
    report = scan(repo, quality, audit)
    assert [(h.start, h.end) for h in report.holes] == [(hour(0), hour(10))]
    assert report.holes[0].expected_candles == 10


def test_full_series_yields_no_hole_and_no_event() -> None:
    repo, quality, audit = harness(list(range(10)))
    report = scan(repo, quality, audit)
    assert report.holes == []
    assert quality.events == []


def test_rescan_is_idempotent() -> None:
    repo, quality, audit = harness([2, 3, 6, 8])
    scan(repo, quality, audit)
    report = scan(repo, quality, audit)

    assert report.new_events == 0
    assert report.already_known == 4
    assert len(quality.list_unresolved(INSTRUMENT.instrument_id, QualityCode.GAP)) == 4


def test_scan_skips_holes_covered_by_known_venue_gap() -> None:
    repo, quality, audit = harness([2, 3, 6, 8])
    scan(repo, quality, audit)
    # venue serves nothing anywhere: every hole becomes KNOWN_VENUE_GAP
    backfill_gaps(GridSource([]), repo, quality, audit, INSTRUMENT, TF, SOURCE)

    report = scan(repo, quality, audit)
    assert report.new_events == 0
    assert all(h.already_known for h in report.holes)
    assert quality.list_unresolved(INSTRUMENT.instrument_id, QualityCode.GAP) == []


def test_misaligned_bounds_are_snapped_to_grid() -> None:
    repo, quality, audit = harness(list(range(10)))
    report = scan(
        repo,
        quality,
        audit,
        start=T0 - TF.duration / 2,  # aligns up to T0
        end=hour(9) + TF.duration / 2,  # aligns down to hour(9)
    )
    assert report.start == T0
    assert report.end == hour(9)
    assert report.holes == []


def test_backfill_fills_hole_and_resolves_gap() -> None:
    repo, quality, audit = harness([0, 1, 8, 9])
    scan(repo, quality, audit)
    venue = GridSource([make_candle(hour(i)) for i in range(10)])

    report = backfill_gaps(venue, repo, quality, audit, INSTRUMENT, TF, SOURCE)

    assert report.gaps_processed == 1
    assert report.inserted == 6
    assert report.filled == 1
    assert report.known_venue_gaps == 0
    assert quality.list_unresolved(INSTRUMENT.instrument_id, QualityCode.GAP) == []
    assert repo.missing_ranges(INSTRUMENT.instrument_id, TF, SOURCE, hour(0), hour(10)) == []
    assert [e.action for e in audit.events[-2:]] == [
        "GAP_BACKFILL_STARTED",
        "GAP_BACKFILL_COMPLETED",
    ]


def test_backfill_reclassifies_venue_empty_subrange() -> None:
    repo, quality, audit = harness([0, 1, 8, 9])  # hole [2,8)
    scan(repo, quality, audit)
    # venue has 2,3 and 6,7 but nothing for [4,6): a maintenance window
    venue = GridSource([make_candle(hour(i)) for i in (2, 3, 6, 7)])

    report = backfill_gaps(venue, repo, quality, audit, INSTRUMENT, TF, SOURCE)

    assert report.inserted == 4
    assert report.filled == 0
    assert report.known_venue_gaps == 1
    assert quality.list_unresolved(INSTRUMENT.instrument_id, QualityCode.GAP) == []
    known = quality.list_unresolved(INSTRUMENT.instrument_id, QualityCode.KNOWN_VENUE_GAP)
    assert len(known) == 1
    assert known[0].severity is QualitySeverity.INFO
    assert known[0].details is not None
    assert known[0].details["gap_start"] == hour(4).isoformat()
    assert known[0].details["gap_end"] == hour(6).isoformat()
    assert "reclassified_from" in known[0].details


def test_backfill_ignores_gaps_of_other_timeframes_and_sources() -> None:
    repo, quality, audit = harness([0, 9])
    scan(repo, quality, audit)  # one GAP for TF/SOURCE
    other = quality.list_unresolved()[0].model_copy(
        update={"event_id": new_id(), "details": {"timeframe": "1d", "source": SOURCE}}
    )
    quality.insert(other)

    report = backfill_gaps(GridSource([]), repo, quality, audit, INSTRUMENT, TF, SOURCE)

    assert report.gaps_processed == 1  # the 1d event was left alone
    unresolved = quality.list_unresolved(INSTRUMENT.instrument_id, QualityCode.GAP)
    assert [e.event_id for e in unresolved] == [other.event_id]


def test_invalid_range_rejected() -> None:
    repo, quality, audit = harness([])
    with pytest.raises(ValueError, match="strictly after"):
        scan(repo, quality, audit, start=T0, end=T0)

"""download_history: chunking, resume from stored data, idempotent reruns."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fakes import InMemoryCandles, RecordingAudit

from quantlab.audit.events import AuditResult
from quantlab.core.ids import new_id
from quantlab.data.download import download_history
from quantlab.data.errors import ConnectorError
from quantlab.domain.models import Candle, Instrument, Timeframe

TF = Timeframe.M1
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


class GridSource:
    """HistoricalCandleSource double serving a fixed candle grid."""

    def __init__(self, open_times: list[datetime]) -> None:
        self.candles = [make_candle(t) for t in sorted(open_times)]
        self.calls: list[tuple[datetime, datetime, int]] = []

    def fetch_candles(
        self,
        instrument: Instrument,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
        limit: int = 1000,
    ) -> list[Candle]:
        self.calls.append((start, end, limit))
        return [c for c in self.candles if start <= c.open_time < end][:limit]

    def health_check(self) -> bool:
        return True


class FailingSource(GridSource):
    """Fails on the second fetch — simulates a venue outage mid-download."""

    def fetch_candles(
        self,
        instrument: Instrument,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
        limit: int = 1000,
    ) -> list[Candle]:
        if len(self.calls) >= 1:
            self.calls.append((start, end, limit))
            raise ConnectorError("venue down")
        return super().fetch_candles(instrument, timeframe, start, end, limit)


def grid(count: int, start: datetime = T0) -> list[datetime]:
    return [start + i * TF.duration for i in range(count)]


def run(
    source: GridSource,
    repo: InMemoryCandles | None = None,
    start: datetime = T0,
    end: datetime = T0 + 10 * TF.duration,
    limit: int = 1000,
) -> tuple[object, InMemoryCandles, RecordingAudit]:
    repo = repo or InMemoryCandles()
    audit = RecordingAudit()
    report = download_history(source, repo, audit, INSTRUMENT, TF, start, end, SOURCE, limit=limit)
    return report, repo, audit


def test_downloads_full_range_in_chunks() -> None:
    source = GridSource(grid(10))
    report, repo, audit = run(source, limit=3)

    assert len(repo.rows) == 10
    assert report.batches == 4  # 3 + 3 + 3 + 1
    assert report.fetched == 10
    assert report.inserted == 10
    assert report.duplicates_skipped == 0
    assert report.resumed_from is None
    # chunks never overlap: each fetch starts after the previous chunk's last candle
    starts = [call[0] for call in source.calls]
    assert starts == sorted(set(starts))
    assert [e.action for e in audit.events] == [
        "HISTORICAL_DOWNLOAD_STARTED",
        "HISTORICAL_DOWNLOAD_COMPLETED",
    ]


def test_resume_starts_after_stored_checkpoint() -> None:
    repo = InMemoryCandles()
    repo.insert_many([make_candle(t) for t in grid(4)])  # first 4 minutes already stored
    source = GridSource(grid(10))

    report, repo, _ = run(source, repo=repo)

    assert source.calls[0][0] == T0 + 4 * TF.duration  # fetch resumes after checkpoint
    assert report.resumed_from == T0 + 3 * TF.duration
    assert report.inserted == 6
    assert len(repo.rows) == 10


def test_rerun_over_covered_range_fetches_nothing() -> None:
    repo = InMemoryCandles()
    repo.insert_many([make_candle(t) for t in grid(10)])
    source = GridSource(grid(10))

    report, _, audit = run(source, repo=repo)

    assert source.calls == []  # checkpoint >= end: not a single API call
    assert report.fetched == 0
    assert report.inserted == 0
    assert audit.events[-1].action == "HISTORICAL_DOWNLOAD_COMPLETED"


def test_venue_gap_is_crossed_not_fatal() -> None:
    times = grid(3) + grid(3, start=T0 + 6 * TF.duration)  # minutes 3-5 missing at the venue
    source = GridSource(times)
    report, repo, _ = run(source, limit=4)

    assert len(repo.rows) == 6
    assert report.inserted == 6


def test_no_data_at_all_completes_with_empty_report() -> None:
    report, repo, audit = run(GridSource([]))
    assert report.batches == 0
    assert repo.rows == {}
    assert audit.events[-1].action == "HISTORICAL_DOWNLOAD_COMPLETED"


def test_failure_mid_download_keeps_progress_and_audits() -> None:
    source = FailingSource(grid(10))
    repo = InMemoryCandles()
    audit = RecordingAudit()

    with pytest.raises(ConnectorError, match="venue down"):
        download_history(
            source, repo, audit, INSTRUMENT, TF, T0, T0 + 10 * TF.duration, SOURCE, limit=3
        )

    assert len(repo.rows) == 3  # first chunk kept — the next run resumes from it
    failure = audit.events[-1]
    assert failure.action == "HISTORICAL_DOWNLOAD_FAILED"
    assert failure.result is AuditResult.FAILURE
    assert repo.latest_open_time(INSTRUMENT.instrument_id, TF, SOURCE) == T0 + 2 * TF.duration


def test_invalid_range_rejected() -> None:
    with pytest.raises(ValueError, match="strictly after"):
        run(GridSource([]), start=T0, end=T0)


def test_naive_datetimes_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        run(GridSource([]), start=datetime(2026, 8, 1), end=T0 + TF.duration)

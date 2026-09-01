"""Replay engine: fail-closed gate, availability ordering, zero look-ahead,
determinism, warm-up marking, snapshot isolation, window bounds."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fakes import (
    InMemoryCandles,
    InMemoryDatasets,
    InMemoryQualityEvents,
    InMemorySnapshotFactory,
    RecordingAudit,
)

from quantlab.core.clock import SimulatedClock
from quantlab.core.ids import new_id
from quantlab.data.datasets import DatasetError, SeriesResolver, freeze_dataset
from quantlab.data.replay import (
    ReplayEvent,
    ReplayIntegrityError,
    ReplayReport,
    SeriesKey,
    replay_candles,
)
from quantlab.domain.models import Candle, DatasetSeries, Instrument, Timeframe, Venue

T0 = datetime(2026, 8, 1, 0, 0, tzinfo=UTC)
SOURCE = "binance"
DAY = T0 + timedelta(days=1)

VENUE = Venue(venue_id=new_id(), code="BINANCE", name="Binance", venue_type="spot")
BTC = Instrument(
    instrument_id=new_id(),
    venue_id=VENUE.venue_id,
    asset_id=None,
    venue_symbol="BTCUSDT",
    instrument_type="spot",
    tick_size=Decimal("0.01"),
    lot_size=Decimal("0.00001"),
)
ETH = BTC.model_copy(update={"instrument_id": new_id(), "venue_symbol": "ETHUSDT"})
INSTRUMENTS = {"BTCUSDT": BTC, "ETHUSDT": ETH}


class Resolver(SeriesResolver):
    def __init__(self) -> None:
        pass

    def __call__(self, series: DatasetSeries) -> tuple[Venue, Instrument]:
        return VENUE, INSTRUMENTS[series.venue_symbol]


def make_candle(instrument: Instrument, timeframe: Timeframe, open_time: datetime) -> Candle:
    return Candle(
        candle_id=new_id(),
        instrument_id=instrument.instrument_id,
        timeframe=timeframe,
        open_time=open_time,
        close_time=open_time + timeframe.duration,
        open=Decimal("100"),
        high=Decimal("101"),
        low=Decimal("99"),
        close=Decimal("100.5"),
        volume=Decimal("1"),
        trade_count=1,
        source=SOURCE,
    )


def full_day(instrument: Instrument) -> list[Candle]:
    """One full day of grid-consistent 1m, 1h and 1d candles."""
    candles = [
        make_candle(instrument, Timeframe.M1, T0 + i * timedelta(minutes=1)) for i in range(1440)
    ]
    candles += [
        make_candle(instrument, Timeframe.H1, T0 + i * timedelta(hours=1)) for i in range(24)
    ]
    candles += [make_candle(instrument, Timeframe.D1, T0)]
    return candles


def build(
    candle_list: list[Candle],
    timeframes: list[Timeframe],
    selections: list[tuple[Venue, Instrument]] | None = None,
):  # type: ignore[no-untyped-def]
    live = InMemoryCandles()
    live.insert_many(candle_list)
    datasets = InMemoryDatasets()
    quality = InMemoryQualityEvents()
    audit = RecordingAudit()
    freeze_dataset(
        live,
        datasets,
        audit,
        "rp",
        "v1",
        selections or [(VENUE, BTC)],
        timeframes,
        T0,
        DAY,
        SOURCE,
    )
    return live, datasets, quality, audit


def run(
    live: InMemoryCandles,
    datasets: InMemoryDatasets,
    quality: InMemoryQualityEvents,
    audit: RecordingAudit,
    clock: SimulatedClock | None = None,
    **kwargs: object,
) -> tuple[list[ReplayEvent], SimulatedClock]:
    clock = clock or SimulatedClock(T0)
    events = list(
        replay_candles(
            InMemorySnapshotFactory(live),
            datasets,
            Resolver(),
            quality,
            audit,
            "rp",
            "v1",
            clock,
            **kwargs,  # type: ignore[arg-type]
        )
    )
    return events, clock


def test_fail_closed_refuses_diverged_dataset_before_any_emission() -> None:
    live, datasets, quality, audit = build(full_day(BTC), [Timeframe.M1, Timeframe.H1])
    live.insert_many(
        [make_candle(BTC, Timeframe.M1, DAY - timedelta(minutes=1) + timedelta(seconds=30))]
    )

    with pytest.raises(ReplayIntegrityError, match="diverged"):
        list(
            replay_candles(
                InMemorySnapshotFactory(live),
                datasets,
                Resolver(),
                quality,
                audit,
                "rp",
                "v1",
                SimulatedClock(T0),
            )
        )
    assert audit.events[-1].action == "REPLAY_REFUSED"
    assert not any(e.action == "REPLAY_STARTED" for e in audit.events)


def test_zero_look_ahead_and_coverage_ordering() -> None:
    """Ta contrainte 2, mot pour mot : à tout instant émis, aucune bougie dont
    close_time > horloge simulée n'a été vue par le consommateur — et une
    bougie n'est émise qu'après toutes celles qu'elle recouvre."""
    live, datasets, quality, audit = build(
        full_day(BTC), [Timeframe.M1, Timeframe.H1, Timeframe.D1]
    )
    events, _clock = run(live, datasets, quality, audit)

    assert len(events) == 1440 + 24 + 1
    seen: list[tuple[Candle, datetime]] = []
    replay_clock = SimulatedClock(T0)
    for event in list(
        replay_candles(
            InMemorySnapshotFactory(live),
            datasets,
            Resolver(),
            quality,
            audit,
            "rp",
            "v1",
            replay_clock,
        )
    ):
        seen.append((event.candle, replay_clock.now()))
    # invariant: nothing seen closes after the clock at its emission instant
    assert all(candle.close_time <= at for candle, at in seen)
    # clock is non-decreasing
    instants = [at for _, at in seen]
    assert instants == sorted(instants)
    # coverage: each 1h candle arrives after the 60 1m candles it covers
    emitted_order = {(c.timeframe, c.open_time): i for i, (c, _) in enumerate(seen)}
    for h in range(24):
        h_open = T0 + h * timedelta(hours=1)
        h_index = emitted_order[(Timeframe.H1, h_open)]
        for m in range(60):
            m_index = emitted_order[(Timeframe.M1, h_open + m * timedelta(minutes=1))]
            assert m_index < h_index
    # and the 1d candle is the very last event of the day
    assert emitted_order[(Timeframe.D1, T0)] == len(seen) - 1


def test_deterministic_stream_hash() -> None:
    live, datasets, quality, audit = build(
        full_day(BTC) + full_day(ETH),
        [Timeframe.M1, Timeframe.H1, Timeframe.D1],
        selections=[(VENUE, BTC), (VENUE, ETH)],
    )

    def stream_hash() -> str:
        events, _ = run(live, datasets, quality, audit)
        digest = hashlib.sha256()
        for event in events:
            c = event.candle
            digest.update(
                f"{c.instrument_id}|{c.timeframe.value}|{c.open_time.isoformat()}"
                f"|{c.close}|{event.is_warmup}\n".encode()
            )
        return digest.hexdigest()

    assert stream_hash() == stream_hash()


def test_warmup_events_are_marked_and_clock_pinned_at_start() -> None:
    live, datasets, quality, audit = build(full_day(BTC), [Timeframe.M1])
    start = T0 + timedelta(hours=6)
    events, _clock = run(live, datasets, quality, audit, start=start, lookback=timedelta(hours=2))

    warmup = [e for e in events if e.is_warmup]
    decision = [e for e in events if not e.is_warmup]
    # 2h of 1m history, all closing in (start-2h, start]
    assert len(warmup) == 120
    assert all(e.candle.close_time <= start for e in warmup)
    assert min(e.candle.close_time for e in warmup) == start - timedelta(hours=2) + timedelta(
        minutes=1
    )
    # warm-up first, then decision candles only
    assert [e.is_warmup for e in events] == [True] * 120 + [False] * len(decision)
    assert all(e.candle.close_time > start for e in decision)
    # 18h remaining in the day
    assert len(decision) == 18 * 60


def test_lookback_truncated_at_dataset_start() -> None:
    live, datasets, quality, audit = build(full_day(BTC), [Timeframe.M1])
    start = T0 + timedelta(hours=1)
    events, _ = run(live, datasets, quality, audit, start=start, lookback=timedelta(days=7))
    warmup = [e for e in events if e.is_warmup]
    assert len(warmup) == 60  # only one hour exists before start
    assert warmup[0].candle.open_time == T0


def test_no_warmup_without_lookback() -> None:
    live, datasets, quality, audit = build(full_day(BTC), [Timeframe.M1])
    events, _ = run(live, datasets, quality, audit, start=T0 + timedelta(hours=6))
    assert all(not e.is_warmup for e in events)
    assert len(events) == 18 * 60


def test_window_end_excludes_crossing_candles() -> None:
    live, datasets, quality, audit = build(full_day(BTC), [Timeframe.M1, Timeframe.H1])
    end = T0 + timedelta(hours=6, minutes=30)
    events, _ = run(live, datasets, quality, audit, end=end)

    hours = [e for e in events if e.candle.timeframe is Timeframe.H1]
    minutes = [e for e in events if e.candle.timeframe is Timeframe.M1]
    assert len(hours) == 6  # the 06:00→07:00 candle is not available before end
    assert len(minutes) == 390
    assert all(e.candle.close_time <= end for e in events)


def test_snapshot_isolation_hides_concurrent_inserts() -> None:
    live, datasets, quality, audit = build(full_day(BTC), [Timeframe.M1])
    clock = SimulatedClock(T0)
    stream = replay_candles(
        InMemorySnapshotFactory(live),
        datasets,
        Resolver(),
        quality,
        audit,
        "rp",
        "v1",
        clock,
    )
    first = [next(stream) for _ in range(10)]
    # concurrent insert lands mid-replay — invisible to the running snapshot
    live.insert_many([make_candle(BTC, Timeframe.M1, T0 + timedelta(days=2))])
    rest = list(stream)
    assert len(first) + len(rest) == 1440


def test_selection_filters_and_rejects_unknown_symbols() -> None:
    live, datasets, quality, audit = build(
        full_day(BTC) + full_day(ETH),
        [Timeframe.M1, Timeframe.H1],
        selections=[(VENUE, BTC), (VENUE, ETH)],
    )
    events, _ = run(live, datasets, quality, audit, symbols=["ETHUSDT"], timeframes=[Timeframe.H1])
    assert len(events) == 24
    assert all(e.candle.instrument_id == ETH.instrument_id for e in events)

    with pytest.raises(DatasetError, match="not part of the dataset"):
        run(live, datasets, quality, audit, symbols=["XRPUSDT"])


def test_window_outside_dataset_rejected() -> None:
    live, datasets, quality, audit = build(full_day(BTC), [Timeframe.M1])
    with pytest.raises(ValueError, match="must sit inside"):
        run(live, datasets, quality, audit, end=DAY + timedelta(hours=1))


def test_events_carry_series_identity() -> None:
    live, datasets, quality, audit = build(
        full_day(BTC) + full_day(ETH),
        [Timeframe.M1, Timeframe.H1],
        selections=[(VENUE, BTC), (VENUE, ETH)],
    )
    events, _ = run(live, datasets, quality, audit)

    by_instrument = {BTC.instrument_id: "BTCUSDT", ETH.instrument_id: "ETHUSDT"}
    for event in events:
        assert event.series == SeriesKey(
            venue="BINANCE",
            venue_symbol=by_instrument[event.candle.instrument_id],
            timeframe=event.candle.timeframe,
            source=SOURCE,
        )


def test_replay_report_final_after_exhaustion() -> None:
    live, datasets, quality, audit = build(full_day(BTC), [Timeframe.M1])
    start = T0 + timedelta(hours=6)
    report = ReplayReport()
    clock = SimulatedClock(T0)
    stream = replay_candles(
        InMemorySnapshotFactory(live),
        datasets,
        Resolver(),
        quality,
        audit,
        "rp",
        "v1",
        clock,
        start=start,
        lookback=timedelta(hours=2),
        report=report,
    )
    next(stream)
    assert not report.completed  # mid-stream: counters are running, not final
    rest = list(stream)

    assert report.completed
    assert report.emitted == 1 + len(rest) == 120 + 18 * 60
    assert report.warmup == 120
    assert report.series == 1
    assert report.start == start
    assert report.end == DAY
    assert report.lookback_start == start - timedelta(hours=2)
    assert report.verify_seconds >= 0
    assert report.stream_seconds >= 0

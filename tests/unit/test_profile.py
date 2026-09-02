"""Volume Profile Engine (docs/07 minimal perimeter): golden synthetic
profile (SS82), bin assignment, frozen tie-breaks, anti look-ahead
(SS69-71), availability timestamp, determinism, day-gap honesty, and the
SS83 edge cases that fit the perimeter."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from quantlab.core.ids import new_id
from quantlab.data.replay import ReplayEvent, SeriesKey
from quantlab.domain.models import Candle, Timeframe
from quantlab.profile import ProfileConfig, VolumeProfileEngine

KEY = SeriesKey(venue="BINANCE", venue_symbol="BTCUSDT", timeframe=Timeframe.M15, source="binance")
INSTRUMENT_ID = new_id()
D1 = date(2026, 1, 1)


def event(day: date, minute: int, low: str, high: str, volume: str) -> ReplayEvent:
    open_time = datetime.combine(day, datetime.min.time(), tzinfo=UTC) + timedelta(minutes=minute)
    lo, hi = Decimal(low), Decimal(high)
    return ReplayEvent(
        candle=Candle(
            candle_id=new_id(),
            instrument_id=INSTRUMENT_ID,
            timeframe=Timeframe.M15,
            open_time=open_time,
            close_time=open_time + timedelta(minutes=15),
            open=lo,
            high=hi,
            low=lo,
            close=hi,
            volume=Decimal(volume),
            source="binance",
        ),
        is_warmup=False,
        series=KEY,
    )


def feed_day(engine: VolumeProfileEngine, day: date, candles: list[tuple[str, str, str]]) -> None:
    for i, (low, high, volume) in enumerate(candles):
        engine.on_event(event(day, 15 * i, low, high, volume))


GOLDEN = [
    ("100", "100", "10"),
    ("101", "101", "20"),
    ("102", "102", "100"),
    ("103", "103", "20"),
    ("104", "104", "10"),
]


def test_golden_profile_poc_and_value_area() -> None:
    # SS82: 100->10, 101->20, 102->100, 103->20, 104->10 with 5 bins of 0.8
    engine = VolumeProfileEngine(ProfileConfig(bins=5))
    feed_day(engine, D1, GOLDEN)
    assert engine.previous(KEY) is None  # developing profile never readable
    engine.on_event(event(D1 + timedelta(days=1), 0, "102", "102", "1"))
    profile = engine.previous(KEY)
    assert profile is not None
    assert profile.day == D1
    assert profile.poc == Decimal("102")  # bin 2 midpoint: 100 + 0.8*2 + 0.4
    # VA target 0.7*160 = 112: POC bin (100) + tie 20/20 -> lower side -> 120
    assert profile.val == Decimal("100.8")  # lower edge of bin 1
    assert profile.vah == Decimal("102.4")  # upper edge of bin 2
    assert profile.total_volume == Decimal("160")
    assert profile.candle_count == 5
    assert profile.data_quality == "CANDLE_ESTIMATED"
    assert profile.available_at == datetime(2026, 1, 2, tzinfo=UTC)


def test_uniform_distribution_splits_volume_by_overlap() -> None:
    # one candle spanning the whole 4-bin range -> exactly 40 per bin,
    # so every bin ties and the POC tie-break picks the LOWEST bin
    engine = VolumeProfileEngine(ProfileConfig(bins=4))
    feed_day(engine, D1, [("100", "104", "160")])
    engine.on_event(event(D1 + timedelta(days=1), 0, "102", "102", "1"))
    profile = engine.previous(KEY)
    assert profile is not None
    assert profile.total_volume == Decimal("160")
    assert profile.poc == Decimal("100.5")  # midpoint of bin 0 (tie -> lowest)
    assert profile.day_low == Decimal("100")
    assert profile.day_high == Decimal("104")


def test_degenerate_day_single_price() -> None:
    engine = VolumeProfileEngine(ProfileConfig(bins=100))
    feed_day(engine, D1, [("100", "100", "5"), ("100", "100", "7")])
    engine.on_event(event(D1 + timedelta(days=1), 0, "100", "100", "1"))
    profile = engine.previous(KEY)
    assert profile is not None
    assert profile.poc == profile.vah == profile.val == Decimal("100")
    assert profile.total_volume == Decimal("12")


def test_zero_volume_day_degenerates_to_poc_bin() -> None:
    engine = VolumeProfileEngine(ProfileConfig(bins=5))
    feed_day(engine, D1, [("100", "104", "0")])
    engine.on_event(event(D1 + timedelta(days=1), 0, "100", "100", "1"))
    profile = engine.previous(KEY)
    assert profile is not None
    assert profile.total_volume == Decimal("0")
    assert profile.poc == Decimal("100.4")  # lowest bin midpoint, VA = that bin
    assert profile.val == Decimal("100")
    assert profile.vah == Decimal("100.8")


def test_anti_look_ahead_day_j_never_mutates_readable_profile() -> None:
    engine = VolumeProfileEngine(ProfileConfig(bins=5))
    feed_day(engine, D1, GOLDEN)
    day2 = D1 + timedelta(days=1)
    engine.on_event(event(day2, 0, "200", "210", "50"))
    frozen = engine.previous(KEY)
    assert frozen is not None and frozen.day == D1
    # more day-2 candles, including extremes far outside day 1's range
    engine.on_event(event(day2, 15, "50", "300", "999"))
    assert engine.previous(KEY) is frozen  # same object, untouched
    # day 2 finalizes only when day 3 arrives, and matches an independent
    # engine fed the same day-2 candles
    engine.on_event(event(day2 + timedelta(days=1), 0, "100", "100", "1"))
    finalized = engine.previous(KEY)
    reference = VolumeProfileEngine(ProfileConfig(bins=5))
    feed_day(reference, day2, [("200", "210", "50"), ("50", "300", "999")])
    reference.on_event(event(day2 + timedelta(days=1), 0, "100", "100", "1"))
    assert finalized == reference.previous(KEY)


def test_missing_day_keeps_stale_profile_with_honest_day_field() -> None:
    engine = VolumeProfileEngine(ProfileConfig(bins=5))
    feed_day(engine, D1, GOLDEN)
    day3 = D1 + timedelta(days=2)  # day 2 entirely absent (venue gap)
    engine.on_event(event(day3, 0, "102", "102", "1"))
    profile = engine.previous(KEY)
    assert profile is not None
    assert profile.day == D1  # staleness visible to the caller
    assert profile.day != day3 - timedelta(days=1)


def test_determinism_same_stream_same_profiles() -> None:
    def build() -> object:
        engine = VolumeProfileEngine()
        feed_day(
            engine, D1, [("100", "110", "3.5"), ("105", "112", "7.25"), ("95.5", "104", "1.125")]
        )
        engine.on_event(event(D1 + timedelta(days=1), 0, "100", "100", "1"))
        return engine.previous(KEY)

    assert build() == build()


def test_config_version_changes_with_parameters() -> None:
    base, other = ProfileConfig(), ProfileConfig(bins=50)
    assert base.config_version != other.config_version
    assert base.config_version == ProfileConfig().config_version

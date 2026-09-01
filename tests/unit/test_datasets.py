"""Dataset registry: canonical serialization (golden), freeze, verify."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fakes import InMemoryCandles, InMemoryDatasets, InMemoryQualityEvents, RecordingAudit

from quantlab.core.ids import new_id
from quantlab.data.datasets import (
    DatasetError,
    SeriesResolver,
    canonical_decimal,
    freeze_dataset,
    verify_dataset,
    verify_series,
)
from quantlab.domain.models import (
    Candle,
    Dataset,
    DatasetSeries,
    Instrument,
    QualityCode,
    Timeframe,
    Venue,
)

TF = Timeframe.H1
T0 = datetime(2026, 8, 1, 0, 0, tzinfo=UTC)
SOURCE = "binance"

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


def make_candle(
    instrument: Instrument,
    open_time: datetime,
    close: str = "100.5",
    trade_count: int | None = 42,
) -> Candle:
    return Candle(
        candle_id=new_id(),
        instrument_id=instrument.instrument_id,
        timeframe=TF,
        open_time=open_time,
        close_time=open_time + TF.duration,
        open=Decimal("100.50"),
        high=Decimal("101.00"),
        low=Decimal("99.9990"),
        close=Decimal(close),
        volume=Decimal("1.10"),
        trade_count=trade_count,
        source=SOURCE,
    )


def hour(i: int) -> datetime:
    return T0 + i * TF.duration


class Resolver(SeriesResolver):
    """Resolver over in-memory fixtures instead of repositories."""

    def __init__(self) -> None:
        pass

    def __call__(self, series: DatasetSeries) -> tuple[Venue, Instrument]:
        return VENUE, {"BTCUSDT": BTC, "ETHUSDT": ETH}[series.venue_symbol]


Harness = tuple[InMemoryCandles, InMemoryDatasets, InMemoryQualityEvents, RecordingAudit]


def harness(candle_list: list[Candle]) -> Harness:
    candles = InMemoryCandles()
    candles.insert_many(candle_list)
    return candles, InMemoryDatasets(), InMemoryQualityEvents(), RecordingAudit()


def freeze(
    candles: InMemoryCandles,
    datasets: InMemoryDatasets,
    audit: RecordingAudit,
    name: str = "ds",
    version: str = "v1",
    selections: list[tuple[Venue, Instrument]] | None = None,
    end: datetime | None = None,
) -> Dataset:
    return freeze_dataset(
        candles,
        datasets,
        audit,
        name,
        version,
        selections or [(VENUE, BTC)],
        [TF],
        T0,
        end or hour(2),
        SOURCE,
        code_commit="abc1234",
    )


def test_canonical_decimal_locked() -> None:
    cases = {
        "1.10": "1.1",
        "1E+2": "100",
        "0.00": "0",
        "1.0010": "1.001",
        "100": "100",
        "0.5000": "0.5",
    }
    for raw, expected in cases.items():
        assert canonical_decimal(Decimal(raw)) == expected, raw


def test_golden_hash_locks_the_qlds_v1_format() -> None:
    """Byte-for-byte lock of the canonical serialization: this hash is
    recomputed here from hand-written lines, independently of the module's
    own serializer. Any format drift breaks this test — that is the point."""
    candles, datasets, _quality, audit = harness(
        [
            make_candle(BTC, hour(0), trade_count=42),
            make_candle(BTC, hour(1), trade_count=None),
        ]
    )
    dataset = freeze(candles, datasets, audit)

    t0_ms = int(hour(0).timestamp() * 1000)
    t1_ms = int(hour(1).timestamp() * 1000)
    expected_stream = (
        "D|qlds-v1\n"
        f"S|BINANCE|BTCUSDT|1h|binance|{T0.isoformat()}|{hour(2).isoformat()}\n"
        f"C|{t0_ms}|100.5|101|99.999|100.5|1.1|42\n"
        f"C|{t1_ms}|100.5|101|99.999|100.5|1.1|-\n"
    ).encode()
    assert dataset.content_hash == hashlib.sha256(expected_stream).hexdigest()
    assert dataset.metadata is not None
    assert dataset.metadata["series"][0]["series_hash"] == dataset.content_hash
    assert dataset.metadata["code_commit"] == "abc1234"
    assert dataset.metadata["total_candles"] == 2


def test_same_content_same_hash_regardless_of_name_and_version() -> None:
    rows = [make_candle(BTC, hour(0)), make_candle(BTC, hour(1))]
    candles_a, datasets_a, _, audit_a = harness(rows)
    candles_b, datasets_b, _, audit_b = harness(rows)

    a = freeze(candles_a, datasets_a, audit_a, name="alpha", version="v1")
    b = freeze(candles_b, datasets_b, audit_b, name="beta", version="v9")

    assert a.content_hash == b.content_hash


def test_hash_independent_of_selection_order() -> None:
    rows = [make_candle(i, hour(h)) for i in (BTC, ETH) for h in range(2)]
    candles_a, datasets_a, _, audit_a = harness(rows)
    candles_b, datasets_b, _, audit_b = harness(rows)

    a = freeze(candles_a, datasets_a, audit_a, selections=[(VENUE, BTC), (VENUE, ETH)])
    b = freeze(candles_b, datasets_b, audit_b, selections=[(VENUE, ETH), (VENUE, BTC)])

    assert a.content_hash == b.content_hash


def test_duplicate_publication_rejected() -> None:
    candles, datasets, _, audit = harness([make_candle(BTC, hour(0))])
    freeze(candles, datasets, audit)
    with pytest.raises(DatasetError, match="already published"):
        freeze(candles, datasets, audit)


def test_verify_ok_on_untouched_data() -> None:
    candles, datasets, quality, audit = harness(
        [make_candle(BTC, hour(0)), make_candle(BTC, hour(1))]
    )
    freeze(candles, datasets, audit)

    report = verify_dataset(candles, datasets, Resolver(), quality, audit, "ds", "v1")

    assert report.ok
    assert report.mismatches == []
    assert audit.events[-1].action == "DATASET_VERIFY_OK"
    assert quality.events == []


def test_late_insertion_fails_count_precheck_and_records_mismatch() -> None:
    candles, datasets, quality, audit = harness([make_candle(BTC, hour(0))])
    freeze(candles, datasets, audit)
    candles.insert_many([make_candle(BTC, hour(1))])  # late insert inside the range

    report = verify_dataset(candles, datasets, Resolver(), quality, audit, "ds", "v1")

    assert not report.ok
    assert [(m.kind, m.expected, m.actual) for m in report.mismatches] == [("count", "1", "2")]
    events = quality.list_unresolved(code=QualityCode.CANDLE_MISMATCH)
    assert len(events) == 1
    assert events[0].details is not None and events[0].details["kind"] == "count"
    assert audit.events[-1].action == "DATASET_VERIFY_FAILED"


def test_same_count_content_change_fails_on_hash() -> None:
    original = make_candle(BTC, hour(1))
    candles, datasets, quality, audit = harness([make_candle(BTC, hour(0)), original])
    freeze(candles, datasets, audit)
    # same open_time, same count, different close — simulates a rewrite
    key = (original.instrument_id, original.timeframe, original.open_time, original.source)
    candles.rows[key] = make_candle(BTC, hour(1), close="100.75")

    report = verify_dataset(candles, datasets, Resolver(), quality, audit, "ds", "v1")

    assert not report.ok
    assert report.mismatches[0].kind == "hash"


def test_verify_series_checks_only_the_requested_series() -> None:
    rows = [make_candle(i, hour(h)) for i in (BTC, ETH) for h in range(2)]
    candles, datasets, quality, audit = harness(rows)
    freeze(candles, datasets, audit, selections=[(VENUE, BTC), (VENUE, ETH)])
    # corrupt ETH inside the range; BTC stays intact
    key = (ETH.instrument_id, TF, hour(0), SOURCE)
    candles.rows[key] = make_candle(ETH, hour(0), close="100.25")

    ok_report = verify_series(
        candles, datasets, Resolver(), quality, audit, "ds", "v1", "BTCUSDT", TF
    )
    bad_report = verify_series(
        candles, datasets, Resolver(), quality, audit, "ds", "v1", "ETHUSDT", TF
    )

    assert ok_report.ok
    assert not bad_report.ok
    with pytest.raises(DatasetError, match="not part of"):
        verify_series(candles, datasets, Resolver(), quality, audit, "ds", "v1", "XRPUSDT", TF)


def test_unknown_dataset_rejected() -> None:
    candles, datasets, quality, audit = harness([])
    with pytest.raises(DatasetError, match="not found"):
        verify_dataset(candles, datasets, Resolver(), quality, audit, "nope", "v1")


def test_empty_selection_rejected() -> None:
    candles, datasets, _, audit = harness([])
    with pytest.raises(DatasetError, match="at least one"):
        freeze_dataset(candles, datasets, audit, "ds", "v1", [], [TF], T0, hour(1), SOURCE)

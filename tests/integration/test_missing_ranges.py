"""PostgresCandleRepository.missing_ranges against a real database: the SQL
window-function path must agree with the in-memory fake's semantics."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from quantlab.core.ids import new_id
from quantlab.domain.models import Candle, Timeframe
from quantlab.storage.postgres.adapter import PostgresCandleRepository

TF = Timeframe.H1
T0 = datetime(2026, 8, 1, 0, 0, tzinfo=UTC)
SOURCE = "binance"


def hour(i: int) -> datetime:
    return T0 + i * TF.duration


def make_candle(instrument_id: uuid.UUID, open_time: datetime) -> Candle:
    return Candle(
        candle_id=new_id(),
        instrument_id=instrument_id,
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


def test_missing_ranges_reports_leading_interior_and_trailing_holes(
    database_url: str, btc_instrument_id: uuid.UUID
) -> None:
    repo = PostgresCandleRepository(database_url)
    stored = [2, 3, 6, 8]  # over [0, 10): holes [0,2) [4,6) [7,8) [9,10)
    assert repo.insert_many([make_candle(btc_instrument_id, hour(i)) for i in stored]) == 4

    holes = repo.missing_ranges(btc_instrument_id, TF, SOURCE, hour(0), hour(10))

    assert holes == [
        (hour(0), hour(2)),
        (hour(4), hour(6)),
        (hour(7), hour(8)),
        (hour(9), hour(10)),
    ]
    # a sub-window sees only its own holes
    assert repo.missing_ranges(btc_instrument_id, TF, SOURCE, hour(2), hour(7)) == [
        (hour(4), hour(6))
    ]
    # an empty series is one big hole
    other_source = repo.missing_ranges(btc_instrument_id, TF, "nosuch", hour(0), hour(3))
    assert other_source == [(hour(0), hour(3))]

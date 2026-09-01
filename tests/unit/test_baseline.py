"""Baseline consumers: next-open execution, strictly-prior breakout window,
warm-up discipline, cost accounting, determinism."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from quantlab.core.ids import new_id
from quantlab.data.replay import ReplayEvent
from quantlab.domain.models import Candle, Instrument, Timeframe
from quantlab.research.baseline import Breakout, BuyAndHold, FillModel, run_experiment

TF = Timeframe.H1
T0 = datetime(2026, 8, 1, 0, 0, tzinfo=UTC)

INSTRUMENT = Instrument(
    instrument_id=new_id(),
    venue_id=new_id(),
    asset_id=None,
    venue_symbol="BTCUSDT",
    instrument_type="spot",
    tick_size=Decimal("0.01"),
    lot_size=Decimal("0.00001"),
)

# frictionless model: prices tell the whole story
FREE = FillModel(taker_fee=Decimal("0"), half_spread=Decimal("0"), initial_capital=Decimal("100"))


def candle(i: int, open_: str, high: str, low: str, close: str) -> Candle:
    open_time = T0 + i * TF.duration
    return Candle(
        candle_id=new_id(),
        instrument_id=INSTRUMENT.instrument_id,
        timeframe=TF,
        open_time=open_time,
        close_time=open_time + TF.duration,
        open=Decimal(open_),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
        volume=Decimal("1"),
        trade_count=1,
        source="binance",
    )


def events(candles: list[Candle], warmup: int = 0) -> list[ReplayEvent]:
    return [ReplayEvent(candle=c, is_warmup=i < warmup) for i, c in enumerate(candles)]


def test_execution_at_next_open_never_at_signal_close() -> None:
    # buy-and-hold signals long at candle 0's close (100); entry must fill at
    # candle 1's OPEN (200), not at 100 — with 100 of capital we get 0.5 unit.
    rows = [
        candle(0, "100", "110", "90", "100"),
        candle(1, "200", "210", "190", "200"),
        candle(2, "200", "210", "190", "200"),
    ]
    result = run_experiment(events(rows), BuyAndHold(), FREE)

    assert result.trades == 2  # entry + final liquidation
    # 0.5 unit marked at 200 -> equity stays 100; had the fill been at the
    # signal close (100), equity would show 200.
    assert result.equity_rows[1][1] == Decimal("100")
    assert result.equity_rows[0][2] == 0  # flat during the signal candle
    assert result.equity_rows[1][2] == 1
    assert result.final_equity == Decimal("100")


def test_breakout_window_is_strictly_prior_to_decision_candle() -> None:
    # prior highs max out at 110; the decision candle prints high=150 and
    # closes at 120: 120 > 110 (prior window) => long. If the window wrongly
    # included the current candle, 120 < 150 would suppress the signal.
    rows = [
        candle(0, "100", "110", "90", "100"),
        candle(1, "100", "105", "95", "100"),
        candle(2, "100", "150", "95", "120"),  # decision candle, its own high excluded
        candle(3, "121", "125", "119", "121"),  # entry fills here at open
    ]
    result = run_experiment(events(rows), Breakout(n=2), FREE)

    assert result.equity_rows[2][2] == 0  # still flat on the signal candle
    assert result.equity_rows[3][2] == 1  # long from the next candle's open
    assert result.trades == 2  # entry + final liquidation


def test_breakout_exit_to_flat_on_prior_low_break() -> None:
    rows = [
        candle(0, "100", "110", "90", "100"),
        candle(1, "100", "112", "95", "111"),  # close 111 > prior high 110 -> long
        candle(2, "111", "113", "92", "93"),  # entry at open 111; close 93 < prior lows -> flat
        candle(3, "93", "95", "92", "94"),  # exit fills at open 93
        candle(4, "94", "96", "92", "95"),
    ]
    result = run_experiment(events(rows), Breakout(n=1), FREE)

    positions = [row[2] for row in result.equity_rows]
    assert positions == [0, 0, 1, 0, 0]
    assert result.trades == 2  # entry + exit, nothing left to liquidate
    # bought at 111, sold at 93 with 100 capital
    expected = Decimal("100") / Decimal("111") * Decimal("93")
    assert result.final_equity == expected


def test_warmup_seeds_window_without_orders_or_equity_rows() -> None:
    rows = [
        candle(0, "100", "110", "90", "100"),  # warm-up
        candle(1, "100", "111", "95", "100"),  # warm-up
        candle(2, "100", "120", "95", "115"),  # decision: 115 > max(110, 111) -> long
        candle(3, "116", "118", "114", "117"),
    ]
    result = run_experiment(events(rows, warmup=2), Breakout(n=2), FREE)

    assert result.bars == 2  # warm-up produced no equity rows
    assert result.equity_rows[0][2] == 0
    assert result.equity_rows[1][2] == 1  # window was seeded by warm-up alone
    assert result.trades == 2


def test_fees_and_half_spread_accounting() -> None:
    fill = FillModel(
        taker_fee=Decimal("0.001"),
        half_spread=Decimal("0.0001"),
        initial_capital=Decimal("10000"),
    )
    rows = [
        candle(0, "100", "110", "90", "100"),
        candle(1, "100", "110", "90", "100"),
        candle(2, "100", "110", "90", "100"),  # flat prices: only costs remain
    ]
    result = run_experiment(events(rows), BuyAndHold(), fill)

    # entry: fee 10 on 10000, buy 9990 at 100*(1+1bp)
    units = Decimal("9990") / (Decimal("100") * Decimal("1.0001"))
    # liquidation at close 100*(1-1bp), fee 0.1% on proceeds
    proceeds = units * Decimal("100") * Decimal("0.9999")
    expected_final = proceeds * Decimal("0.999")
    assert result.final_equity == expected_final
    assert result.fees_paid == Decimal("10") + proceeds * Decimal("0.001")
    assert result.net_return_pct < 0  # a round trip is never free


def test_deterministic_metrics_and_curve() -> None:
    rows = [candle(i, "100", str(110 + i * 3), "90", str(100 + i * 3)) for i in range(10)]
    a = run_experiment(events(rows, warmup=2), Breakout(n=2), FillModel())
    b = run_experiment(events(rows, warmup=2), Breakout(n=2), FillModel())
    assert a.metrics() == b.metrics()
    assert a.equity_rows == b.equity_rows


def test_empty_stream_yields_flat_result() -> None:
    result = run_experiment([], BuyAndHold(), FREE)
    assert result.bars == 0
    assert result.trades == 0
    assert result.final_equity == FREE.initial_capital
    assert result.net_return_pct == 0


def test_breakout_rejects_bad_window() -> None:
    with pytest.raises(ValueError, match=">= 1"):
        Breakout(n=0)

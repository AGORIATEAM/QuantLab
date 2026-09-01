"""Baseline experiment consumers for the replay stream (T7bis, docs/21).

These are BASELINES (docs/21 §20-§22): trivial, frozen hypotheses whose only
purpose is to (a) reference-point future comparisons and (b) exercise the T7
contract (ReplayEvent / warm-up / determinism) with a real consumer. No
optimization, no financial conclusion.

Fill model — recorded verbatim in every experiment.json, because future
comparisons are only valid at identical model:
- A signal is computed at the CLOSE of a decision candle; the resulting
  position change executes at the OPEN of the NEXT decision candle — never
  at the close of the signal candle.
- Cost per side: taker fee (Binance spot 0.10% default) on the notional,
  plus a fixed half-spread applied to the execution price.
- All-in: the whole cash balance buys; the whole position sells.
- Equity convention: mark-to-market at each decision candle close; the
  final net return additionally liquidates any open position at the last
  close (with costs). The CSV curve is pure mark-to-market.

Warm-up events (is_warmup=True) feed indicator state only: no signal, no
order, no equity row.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from quantlab.data.replay import ReplayEvent
from quantlab.domain.models import Candle

ZERO = Decimal("0")


@dataclass(frozen=True)
class FillModel:
    taker_fee: Decimal = Decimal("0.001")  # Binance spot taker, 10 bps
    half_spread: Decimal = Decimal("0.0001")  # 1 bp per side
    initial_capital: Decimal = Decimal("10000")  # USDT, all-in

    def as_record(self) -> dict[str, object]:
        return {
            "execution": "open of the candle following the signal candle",
            "taker_fee": str(self.taker_fee),
            "half_spread": str(self.half_spread),
            "initial_capital": str(self.initial_capital),
            "sizing": "all-in",
            "equity_convention": {
                "curve": "mark-to-market at each decision candle close",
                "final_liquidation": "net return liquidates any open position "
                "at the last close, with costs",
            },
        }


class BuyAndHold:
    """Always long: the signal is 1 at every decision close, so the single
    entry executes at the open of the second decision candle."""

    def observe(self, candle: Candle) -> None:  # no state to seed
        pass

    def signal(self, candle: Candle) -> int | None:
        return 1


class Breakout:
    """Naive breakout: long when close exceeds the highest high of the N
    candles STRICTLY BEFORE the decision candle, flat when close drops below
    their lowest low. The current candle NEVER belongs to its own window:
    signal() reads the window first, observe() appends after."""

    def __init__(self, n: int) -> None:
        if n < 1:
            raise ValueError("breakout window must be >= 1")
        self.n = n
        self._highs: deque[Decimal] = deque(maxlen=n)
        self._lows: deque[Decimal] = deque(maxlen=n)

    def observe(self, candle: Candle) -> None:
        self._highs.append(candle.high)
        self._lows.append(candle.low)

    def signal(self, candle: Candle) -> int | None:
        if len(self._highs) < self.n:
            return None  # window not seeded yet: no opinion
        if candle.close > max(self._highs):
            return 1
        if candle.close < min(self._lows):
            return 0
        return None  # keep current position


@dataclass
class ExperimentResult:
    equity_rows: list[tuple[datetime, Decimal, int]] = field(default_factory=list)
    trades: int = 0
    fees_paid: Decimal = ZERO
    bars: int = 0
    bars_long: int = 0
    final_equity: Decimal = ZERO
    initial_capital: Decimal = ZERO

    @property
    def net_return_pct(self) -> Decimal:
        if not self.initial_capital:
            return ZERO
        return (self.final_equity / self.initial_capital - 1) * 100

    @property
    def max_drawdown_pct(self) -> Decimal:
        peak = ZERO
        worst = ZERO
        for _, equity, _ in self.equity_rows:
            peak = max(peak, equity)
            if peak > 0:
                worst = min(worst, (equity / peak - 1) * 100)
        return worst

    @property
    def exposure_pct(self) -> Decimal:
        if not self.bars:
            return ZERO
        return Decimal(self.bars_long) / Decimal(self.bars) * 100

    def metrics(self) -> dict[str, object]:
        return {
            "net_return_pct": str(self.net_return_pct.quantize(Decimal("0.01"))),
            "max_drawdown_pct": str(self.max_drawdown_pct.quantize(Decimal("0.01"))),
            "trades": self.trades,
            "fees_paid": str(self.fees_paid.quantize(Decimal("0.01"))),
            "exposure_pct": str(self.exposure_pct.quantize(Decimal("0.01"))),
            "bars": self.bars,
            "final_equity": str(self.final_equity.quantize(Decimal("0.01"))),
        }


def run_experiment(
    events: Iterable[ReplayEvent] | Iterator[ReplayEvent],
    strategy: BuyAndHold | Breakout,
    fill: FillModel,
) -> ExperimentResult:
    """Consume one series of ReplayEvents under the fill model. Time only
    ever comes from the candles the replay emits — never from utc_now()."""
    result = ExperimentResult(initial_capital=fill.initial_capital)
    cash = fill.initial_capital
    units = ZERO
    position = 0
    pending: int | None = None
    last_close: Decimal | None = None

    for event in events:
        candle = event.candle
        if event.is_warmup:
            strategy.observe(candle)  # seed indicators; no order, no equity row
            continue

        # 1. execute the target decided at the PREVIOUS close, at THIS open
        if pending is not None and pending != position:
            if pending == 1:
                price = candle.open * (1 + fill.half_spread)
                fee = cash * fill.taker_fee
                units = (cash - fee) / price
                result.fees_paid += fee
                cash = ZERO
            else:
                proceeds = units * candle.open * (1 - fill.half_spread)
                fee = proceeds * fill.taker_fee
                cash = proceeds - fee
                result.fees_paid += fee
                units = ZERO
            position = pending
            result.trades += 1
        pending = None

        # 2. signal at close — the strategy window excludes the current
        #    candle (observe comes after signal, by construction)
        signal = strategy.signal(candle)
        strategy.observe(candle)
        if signal is not None:
            pending = signal

        # 3. mark to market at close
        equity = cash + units * candle.close
        result.equity_rows.append((candle.close_time, equity, position))
        result.bars += 1
        result.bars_long += position
        last_close = candle.close

    # final liquidation for the net figure (curve stays mark-to-market)
    final = cash
    if units > 0 and last_close is not None:
        proceeds = units * last_close * (1 - fill.half_spread)
        fee = proceeds * fill.taker_fee
        result.fees_paid += fee
        final = cash + proceeds - fee
        result.trades += 1
    result.final_equity = final if result.bars else fill.initial_capital
    return result

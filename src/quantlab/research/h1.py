"""EXP-20260901-003 (H1) runner: 5m structure breaks aligned with the 1h
structure, under the amended pre-registered fill model.

Rules (frozen in experiments/EXP-20260901-003.../experiment.json):
- direction = 1h structure state (BULLISH -> longs only, BEARISH -> shorts
  only, NEUTRAL/UNKNOWN -> no trade);
- entry = strict 5m BOS in that direction, filled at the NEXT 5m open;
- stop = last kept opposite 5m swing at signal time; if the stop distance
  at signal is < min_stop_atr x ATR_5m the trade is SKIPPED (never
  widened);
- exit = target at entry ± r_target x initial stop distance, or a 5m
  CHoCH against the position (signal at close, filled at the next open);
- pessimistic ambiguities: same-candle stop AND target -> stop first;
  an open gapping beyond the stop fills at the OPEN; one position per
  symbol, no pyramiding, signals ignored while in position;
- sizing: risk 0.5% of equity / stop distance, notional capped at 1x
  equity (spot); entry+exit costs = taker fee + half-spread per side.

One replay pass per (instrument, period) feeds every configuration:
engines are shared across configurations that only differ by r_target /
min_stop_atr. Equity is marked to market per 5m candle; daily samples
feed the annualized Sharpe; nothing but metrics is kept per config.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from quantlab.core.logging import get_logger
from quantlab.data.replay import ReplayEvent, SeriesKey
from quantlab.domain.models import Candle
from quantlab.research.baseline import FillModel
from quantlab.structure.breaks import BreakDirection, BreakKind, ValidationMethod
from quantlab.structure.engine import (
    DetectorKind,
    MarketStructureEngine,
    StructureConfig,
    StructureEvent,
    StructureEventType,
)
from quantlab.structure.state import StructureState
from quantlab.structure.swings import SwingKind

logger = get_logger(__name__)

ZERO = Decimal(0)


@dataclass(frozen=True)
class H1Config:
    n_5m: int
    n_1h: int
    atr_multiplier: Decimal
    breakout_buffer: Decimal
    r_target: Decimal
    min_stop_atr: Decimal

    def label(self) -> str:
        return (
            f"n5m={self.n_5m} n1h={self.n_1h} mult={self.atr_multiplier} "
            f"buf={self.breakout_buffer} R={self.r_target} minstop={self.min_stop_atr}"
        )

    def engine_config(self, n: int) -> StructureConfig:
        return StructureConfig(
            detector=DetectorKind.ATR,
            n=n,
            atr_multiplier=self.atr_multiplier,
            validation=(
                ValidationMethod.ATR_BUFFER if self.breakout_buffer > 0 else ValidationMethod.CLOSE
            ),
            breakout_buffer=self.breakout_buffer,
        )


@dataclass
class _Position:
    side: int  # +1 long, -1 short
    qty: Decimal
    entry: Decimal  # spread-adjusted fill price
    stop: Decimal
    target: Decimal
    initial_risk: Decimal  # quote currency at entry
    fees: Decimal  # entry fee (exit fee added at close), quote currency
    spread_cost: Decimal  # explicit half-spread cost for the cost metric


@dataclass
class H1Metrics:
    trades: int = 0
    wins: int = 0
    gross_profit: Decimal = ZERO
    gross_loss: Decimal = ZERO
    sum_r: Decimal = ZERO
    sum_cost_r: Decimal = ZERO
    sum_stop_pct: Decimal = ZERO
    fees_paid: Decimal = ZERO
    capped: int = 0
    skipped_min_stop: int = 0
    ignored_in_position: int = 0
    bars: int = 0
    bars_in_position: int = 0
    final_equity: Decimal = ZERO
    max_drawdown_pct: Decimal = ZERO
    sharpe_annualized: float | None = None


class H1Simulator:
    """One configuration's trade loop over the 5m stream. The structure
    engines are shared and read-only from here."""

    def __init__(
        self,
        config: H1Config,
        engine_5m: MarketStructureEngine,
        engine_1h: MarketStructureEngine,
        key_5m: SeriesKey,
        key_1h: SeriesKey,
        fill: FillModel,
    ) -> None:
        self.config = config
        self._engine_5m = engine_5m
        self._engine_1h = engine_1h
        self._key_5m = key_5m
        self._key_1h = key_1h
        self._fill = fill
        self._equity = fill.initial_capital
        self._position: _Position | None = None
        self._entry_pending: tuple[int, Decimal] | None = None  # (side, stop)
        self._exit_pending = False
        self._peak = ZERO
        self._max_dd = ZERO
        self._last_day: date | None = None
        self._daily: list[Decimal] = []
        self._last_close: Decimal | None = None
        self.metrics = H1Metrics()

    # -- fills ---------------------------------------------------------------

    def _buy_price(self, price: Decimal) -> Decimal:
        return price * (1 + self._fill.half_spread)

    def _sell_price(self, price: Decimal) -> Decimal:
        return price * (1 - self._fill.half_spread)

    def _open_position(self, side: int, raw_price: Decimal, stop: Decimal) -> None:
        price = self._buy_price(raw_price) if side > 0 else self._sell_price(raw_price)
        distance = (price - stop) * side
        if distance <= 0:
            return  # the fill already sits beyond the stop: no trade
        qty = (self._equity * Decimal("0.005")) / distance
        if qty * price > self._equity:  # spot cap: 1x equity notional
            qty = self._equity / price
            self.metrics.capped += 1
        fee = qty * price * self._fill.taker_fee
        self._position = _Position(
            side=side,
            qty=qty,
            entry=price,
            stop=stop,
            target=price + side * self.config.r_target * distance,
            initial_risk=qty * distance,
            fees=fee,
            spread_cost=qty * raw_price * self._fill.half_spread,
        )
        self.metrics.fees_paid += fee

    def _close_position(self, raw_price: Decimal) -> None:
        position = self._position
        assert position is not None
        price = self._sell_price(raw_price) if position.side > 0 else self._buy_price(raw_price)
        fee = position.qty * price * self._fill.taker_fee
        self.metrics.fees_paid += fee
        # spread is embedded in the fill prices (never double-counted in pnl);
        # the cost METRIC reports it explicitly: fees both sides + both spreads
        total_costs = position.fees + fee + position.spread_cost
        total_costs += position.qty * raw_price * self._fill.half_spread
        pnl = position.side * position.qty * (price - position.entry) - fee - position.fees
        self._equity += pnl
        m = self.metrics
        m.trades += 1
        if pnl > 0:
            m.wins += 1
            m.gross_profit += pnl
        else:
            m.gross_loss += -pnl
        if position.initial_risk > 0:
            m.sum_r += pnl / position.initial_risk
            m.sum_cost_r += total_costs / position.initial_risk
        m.sum_stop_pct += abs(position.entry - position.stop) / position.entry * 100
        self._position = None

    # -- per-candle ----------------------------------------------------------

    def on_5m(self, event: ReplayEvent, structure_events: list[StructureEvent]) -> None:
        candle = event.candle
        if event.is_warmup:
            return
        # 1. pending CHoCH exit fills at this open
        if self._position is not None and self._exit_pending:
            self._close_position(candle.open)
            self._exit_pending = False
        # 2. pending entry fills at this open
        if self._position is None and self._entry_pending is not None:
            side, stop = self._entry_pending
            self._open_position(side, candle.open, stop)
        self._entry_pending = None
        # 3. stop / target on this candle — stop first (pessimistic)
        position = self._position
        if position is not None:
            if position.side > 0:
                if candle.open <= position.stop:
                    self._close_position(candle.open)  # gap rule: fill at the open
                elif candle.low <= position.stop:
                    self._close_position(position.stop)
                elif candle.high >= position.target:
                    self._close_position(position.target)
            else:
                if candle.open >= position.stop:
                    self._close_position(candle.open)
                elif candle.high >= position.stop:
                    self._close_position(position.stop)
                elif candle.low <= position.target:
                    self._close_position(position.target)
        # 4. signals at this close
        self._signals(structure_events, candle)
        # 5. mark to market, daily sampling, exposure
        self._mark(candle)

    def _signals(self, structure_events: list[StructureEvent], candle: Candle) -> None:
        h1_state = self._engine_1h.state_of(self._key_1h)
        for out in structure_events:
            if out.event_type is not StructureEventType.STRUCTURE_BREAK or out.brk is None:
                continue
            brk = out.brk
            if brk.kind is BreakKind.CHOCH and self._position is not None:
                against = (
                    brk.direction is BreakDirection.BEARISH
                    if self._position.side > 0
                    else brk.direction is BreakDirection.BULLISH
                )
                if against:
                    self._exit_pending = True
            if brk.kind is not BreakKind.BOS:
                continue
            if self._position is not None or self._entry_pending is not None:
                self.metrics.ignored_in_position += 1
                continue
            if h1_state is StructureState.BULLISH and brk.direction is BreakDirection.BULLISH:
                side = 1
            elif h1_state is StructureState.BEARISH and brk.direction is BreakDirection.BEARISH:
                side = -1
            else:
                continue
            runtime = self._engine_5m.runtime(self._key_5m)
            stop_swing = runtime.sequence.last(SwingKind.LOW if side > 0 else SwingKind.HIGH)
            if stop_swing is None:
                continue
            stop = stop_swing.price
            distance = (candle.close - stop) * side
            if distance <= 0:
                continue
            atr = runtime.detector.atr.value
            if atr is not None and distance < self.config.min_stop_atr * atr:
                self.metrics.skipped_min_stop += 1
                continue
            self._entry_pending = (side, stop)

    def _mark(self, candle: Candle) -> None:
        m = self.metrics
        m.bars += 1
        equity = self._equity
        if self._position is not None:
            m.bars_in_position += 1
            p = self._position
            equity += p.side * p.qty * (candle.close - p.entry) - p.fees
        self._peak = max(self._peak, equity)
        if self._peak > 0:
            self._max_dd = min(self._max_dd, (equity / self._peak - 1) * 100)
        day = candle.close_time.date()
        if self._last_day is None:
            self._last_day = day
        elif day != self._last_day:
            self._daily.append(equity)
            self._last_day = day
        self._last_close = candle.close

    def finalize(self) -> H1Metrics:
        if self._position is not None and self._last_close is not None:
            self._close_position(self._last_close)  # final liquidation convention
        m = self.metrics
        m.final_equity = self._equity
        m.max_drawdown_pct = self._max_dd
        if len(self._daily) > 2:
            returns = [
                float(b / a - 1)
                for a, b in zip(self._daily, self._daily[1:], strict=False)
                if a > 0
            ]
            if returns:
                mean = sum(returns) / len(returns)
                var = sum((r - mean) ** 2 for r in returns) / len(returns)
                std = var**0.5
                m.sharpe_annualized = (mean / std * (365**0.5)) if std > 0 else None
        return m

"""Float64 hot-loop mirrors for EXP-20260901-003 (ADR-0003 décision 2).

SANCTIONED FLOAT PERIMETER. Every rule mirrors the Decimal references
byte for byte in behavior — quantlab/structure/* for the engine,
quantlab/research/h1.py for the simulator — and the two ADR-0003
equivalence levels are the proof. Any rule change lands in the Decimal
reference FIRST, then here.

Deliberate deviations with zero behavioral impact on H1:
- WICK_BREAK events ARE mirrored (H2 consumes them; once per armed swing,
  never consuming the level — H1 ignores them, proven by the unchanged
  golden SHA after their introduction);
- the swing sequence keeps only its last 4 entries (alternation
  guarantees they are 2 highs + 2 lows, all the state machine reads);
- structure events are returned as plain (kind, direction) pairs.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

# state
UNKNOWN, BULLISH, BEARISH, NEUTRAL = 0, 1, 2, 3
# swing kinds / break kinds / directions
HIGH, LOW = 0, 1
BOS, CHOCH, WICK = 0, 1, 2  # unclassified breaks consume the level but emit nothing


class FastAtr:
    """Mirror of structure.atr.WilderAtr."""

    def __init__(self, period: int = 14) -> None:
        self.period = period
        self._previous_close: float | None = None
        self._warmup: list[float] = []
        self.value: float | None = None

    def update(self, high: float, low: float, close: float) -> None:
        if self._previous_close is None:
            tr = high - low
        else:
            tr = max(high - low, abs(high - self._previous_close), abs(low - self._previous_close))
        self._previous_close = close
        if self.value is None:
            self._warmup.append(tr)
            if len(self._warmup) == self.period:
                self.value = sum(self._warmup) / self.period
        else:
            self.value = (self.value * (self.period - 1) + tr) / self.period


class FastStructure:
    """Mirror of MarketStructureEngine for ONE series with the ATR swing
    detector (the only detector H1 uses): fractal candidates, alternating
    sequence with the min-leg filter, state machine, BOS/CHoCH with level
    consumption, readiness gate with the announce-candle swallowing."""

    def __init__(
        self, n: int, atr_multiplier: float, breakout_buffer: float, filter_legs: bool = True
    ) -> None:
        self.n = n
        self.mult = atr_multiplier
        self.buffer = breakout_buffer  # 0 -> close validation (method A)
        self.filter_legs = filter_legs  # False -> fractal detector (no ATR min-leg)
        self.atr = FastAtr(14)
        self._window: deque[tuple[float, float]] = deque(maxlen=2 * n + 1)  # (high, low)
        self._swings: list[tuple[int, float]] = []  # (kind, price), alternating, capped at 4
        self.state = UNKNOWN
        self._announced = False
        self._armed: list[list[float | bool] | None] = [None, None]  # [level, wick_flagged]
        self.last_high: float | None = None
        self.last_low: float | None = None

    # -- swings -------------------------------------------------------------

    def _push(self, kind: int, price: float) -> bool:
        """SwingSequence.push mirror; returns True when the sequence changed."""
        last = self._swings[-1] if self._swings else None
        if last is not None and last[0] == kind:
            more_extreme = price > last[1] if kind == HIGH else price < last[1]
            if not more_extreme:
                return False
            self._swings[-1] = (kind, price)
        else:
            if self.filter_legs and last is not None:  # ATR min-leg from the opposite swing
                min_leg = None if self.atr.value is None else self.atr.value * self.mult
                if min_leg is not None and abs(price - last[1]) < min_leg:
                    return False
            self._swings.append((kind, price))
            if len(self._swings) > 4:
                self._swings.pop(0)
        if kind == HIGH:
            self.last_high = price
        else:
            self.last_low = price
        self._armed[kind] = [price, False]  # arm/re-arm the level (règle 4)
        return True

    def _derive_state(self) -> int:
        highs = [p for k, p in self._swings if k == HIGH]
        lows = [p for k, p in self._swings if k == LOW]
        if len(highs) < 2 or len(lows) < 2:
            return UNKNOWN
        hh = highs[-1] > highs[-2]
        hl = lows[-1] > lows[-2]
        if hh and hl:
            return BULLISH
        if not hh and not hl:
            return BEARISH
        return NEUTRAL

    @property
    def ready(self) -> bool:
        return (
            self.atr.value is not None
            and len(self._window) == self._window.maxlen
            and sum(1 for k, _ in self._swings if k == HIGH) >= 2
            and sum(1 for k, _ in self._swings if k == LOW) >= 2
        )

    def state_of(self) -> int:
        return self.state if self.ready else UNKNOWN

    # -- per candle ---------------------------------------------------------

    def update(self, o: float, h: float, lo: float, c: float) -> list[tuple[int, int, float]]:
        """Returns [(BOS|CHOCH|WICK, direction, break_price), ...] for this
        close — break_price mirrors the slow BreakEvent (the close for a
        validated break, the wick extreme for a WICK_BREAK)."""
        self.atr.update(h, lo, c)
        self._window.append((h, lo))
        if len(self._window) == self._window.maxlen:
            window = list(self._window)
            center_h, center_l = window[self.n]
            before = window[: self.n]
            after = window[self.n + 1 :]
            if all(center_h > wh for wh, _ in before) and all(center_h >= wh for wh, _ in after):
                if self._push(HIGH, center_h):
                    self.state = self._derive_state()
            if all(center_l < wl for _, wl in before) and all(center_l <= wl for _, wl in after):
                if self._push(LOW, center_l):
                    self.state = self._derive_state()

        if not self.ready:
            return []
        if not self._announced:
            self._announced = True
            return []  # the announce candle emits only the state snapshot
        events: list[tuple[int, int, float]] = []
        atr = self.atr.value
        for kind, direction in ((HIGH, BULLISH), (LOW, BEARISH)):
            armed = self._armed[kind]
            if armed is None:
                continue
            level = float(armed[0])
            threshold = level + (atr or 0.0) * self.buffer * (1 if kind == HIGH else -1)
            validated = c > threshold if kind == HIGH else c < threshold
            wicked = (h > level) if kind == HIGH else (lo < level)
            if validated:
                self._armed[kind] = None  # consumed, even when unclassified
                if kind == HIGH:
                    out = (
                        BOS if self.state == BULLISH else (CHOCH if self.state == BEARISH else None)
                    )
                else:
                    out = (
                        BOS if self.state == BEARISH else (CHOCH if self.state == BULLISH else None)
                    )
                if out is not None:
                    events.append((out, direction, c))
            elif wicked and not armed[1]:
                armed[1] = True  # once per armed swing; the level stays armed
                events.append((WICK, direction, h if kind == HIGH else lo))
        return events


@dataclass
class FastMetrics:
    trades: int = 0
    wins: int = 0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    sum_r: float = 0.0
    sum_cost_r: float = 0.0
    sum_stop_pct: float = 0.0
    fees_paid: float = 0.0
    capped: int = 0
    skipped_min_stop: int = 0
    ignored_in_position: int = 0
    bars: int = 0
    bars_in_position: int = 0
    final_equity: float = 0.0
    max_drawdown_pct: float = 0.0
    sharpe_annualized: float | None = None


@dataclass
class _FastPosition:
    side: int
    qty: float
    entry: float
    stop: float
    target: float
    initial_risk: float
    fees: float
    spread_cost: float
    entry_ots: int


class FastSimulator:
    """Mirror of research.h1.H1Simulator, float64, same step order:
    1 pending CHoCH exit at open, 2 pending entry at open, 3 stop/target
    (gap at open, stop first), 4 signals at close, 5 mark to market."""

    TAKER = 0.001
    HALF_SPREAD = 0.0001
    CAPITAL = 10_000.0
    RISK = 0.005

    def __init__(
        self,
        r_target: float,
        min_stop_atr: float,
        structure_5m: FastStructure,
        structure_1h: FastStructure,
        log_trades: bool = False,
    ) -> None:
        self.r_target = r_target
        self.min_stop_atr = min_stop_atr
        self.s5 = structure_5m
        self.s1 = structure_1h
        self._equity = self.CAPITAL
        self._position: _FastPosition | None = None
        self._entry_pending: tuple[int, float] | None = None
        self._exit_pending = False
        self._peak = 0.0
        self._max_dd = 0.0
        self._last_day: int | None = None
        self._daily: list[float] = []
        self._last_close: float | None = None
        self._current_ots = 0
        self.metrics = FastMetrics()
        self.trade_log: list[tuple[int, int, int, float, float, float]] | None = (
            [] if log_trades else None
        )

    def _open_position(self, side: int, raw: float, stop: float, ots: int) -> None:
        price = raw * (1 + self.HALF_SPREAD) if side > 0 else raw * (1 - self.HALF_SPREAD)
        distance = (price - stop) * side
        if distance <= 0:
            return
        qty = (self._equity * self.RISK) / distance
        if qty * price > self._equity:
            qty = self._equity / price
            self.metrics.capped += 1
        fee = qty * price * self.TAKER
        self._position = _FastPosition(
            side,
            qty,
            price,
            stop,
            price + side * self.r_target * distance,
            qty * distance,
            fee,
            qty * raw * self.HALF_SPREAD,
            ots,
        )
        self.metrics.fees_paid += fee

    def _close_position(self, raw: float) -> None:
        p = self._position
        assert p is not None
        price = raw * (1 - self.HALF_SPREAD) if p.side > 0 else raw * (1 + self.HALF_SPREAD)
        fee = p.qty * price * self.TAKER
        self.metrics.fees_paid += fee
        total_costs = p.fees + fee + p.spread_cost + p.qty * raw * self.HALF_SPREAD
        pnl = p.side * p.qty * (price - p.entry) - fee - p.fees
        self._equity += pnl
        m = self.metrics
        m.trades += 1
        if pnl > 0:
            m.wins += 1
            m.gross_profit += pnl
        else:
            m.gross_loss += -pnl
        r = 0.0
        if p.initial_risk > 0:
            r = pnl / p.initial_risk
            m.sum_r += r
            m.sum_cost_r += total_costs / p.initial_risk
        m.sum_stop_pct += abs(p.entry - p.stop) / p.entry * 100
        if self.trade_log is not None:
            self.trade_log.append((p.entry_ots, self._current_ots, p.side, p.entry, price, r))
        self._position = None

    def on_5m(
        self,
        warmup: bool,
        ots: int,
        o: float,
        h: float,
        lo: float,
        c: float,
        events: list[tuple[int, int, float]],
    ) -> None:
        if warmup:
            return
        self._current_ots = ots
        if self._position is not None and self._exit_pending:
            self._close_position(o)
            self._exit_pending = False
        if self._position is None and self._entry_pending is not None:
            side, stop = self._entry_pending
            self._open_position(side, o, stop, ots)
        self._entry_pending = None
        p = self._position
        if p is not None:
            if p.side > 0:
                if o <= p.stop:
                    self._close_position(o)
                elif lo <= p.stop:
                    self._close_position(p.stop)
                elif h >= p.target:
                    self._close_position(p.target)
            else:
                if o >= p.stop:
                    self._close_position(o)
                elif h >= p.stop:
                    self._close_position(p.stop)
                elif lo <= p.target:
                    self._close_position(p.target)
        self._signals(events, c)
        self._mark(ots, c)

    def _signals(self, events: list[tuple[int, int, float]], close: float) -> None:
        h1_state = self.s1.state_of()
        for kind, direction, _price in events:
            if kind == CHOCH and self._position is not None:
                against = direction == BEARISH if self._position.side > 0 else direction == BULLISH
                if against:
                    self._exit_pending = True
            if kind != BOS:
                continue
            if self._position is not None or self._entry_pending is not None:
                self.metrics.ignored_in_position += 1
                continue
            if h1_state == BULLISH and direction == BULLISH:
                side = 1
            elif h1_state == BEARISH and direction == BEARISH:
                side = -1
            else:
                continue
            stop = self.s5.last_low if side > 0 else self.s5.last_high
            if stop is None:
                continue
            distance = (close - stop) * side
            if distance <= 0:
                continue
            atr = self.s5.atr.value
            if atr is not None and distance < self.min_stop_atr * atr:
                self.metrics.skipped_min_stop += 1
                continue
            self._entry_pending = (side, stop)

    def _mark(self, ots: int, close: float) -> None:
        m = self.metrics
        m.bars += 1
        equity = self._equity
        if self._position is not None:
            m.bars_in_position += 1
            p = self._position
            equity += p.side * p.qty * (close - p.entry) - p.fees
        if equity > self._peak:
            self._peak = equity
        if self._peak > 0:
            dd = (equity / self._peak - 1) * 100
            if dd < self._max_dd:
                self._max_dd = dd
        day = (ots + 300) // 86400  # close_time = open + 300s, same day rule as slow
        if self._last_day is None:
            self._last_day = day
        elif day != self._last_day:
            self._daily.append(equity)
            self._last_day = day
        self._last_close = close

    def finalize(self) -> FastMetrics:
        if self._position is not None and self._last_close is not None:
            self._close_position(self._last_close)
        m = self.metrics
        m.final_equity = self._equity
        m.max_drawdown_pct = self._max_dd
        if len(self._daily) > 2:
            returns = [
                b / a - 1 for a, b in zip(self._daily, self._daily[1:], strict=False) if a > 0
            ]
            if returns:
                mean = sum(returns) / len(returns)
                std = (sum((r - mean) ** 2 for r in returns) / len(returns)) ** 0.5
                m.sharpe_annualized = mean / std * 365**0.5 if std > 0 else None
        return m


@dataclass
class FastContext:
    """ContextStats mirror for one 1h structure."""

    bars: int = 0
    neutral: int = 0
    changes: int = 0
    previous: int = field(default=-1)

    def observe(self, state: int) -> None:
        if state == UNKNOWN:
            return
        self.bars += 1
        if state == NEUTRAL:
            self.neutral += 1
        if self.previous != -1 and state != self.previous:
            self.changes += 1
        self.previous = state


def run_shard(
    rows: list[tuple[bool, bool, int, float, float, float, float]],
    configs: list[tuple[int, int, int, float, float, float, float]],
    log_trades: bool = False,
) -> list[tuple[int, FastMetrics, FastContext, object]]:
    """Run a shard of configurations over the extracted rows.
    Each config: (index, n_5m, n_1h, mult, buffer, r_target, min_stop).
    Returns (index, metrics, 1h-context, trade_log) per config, in shard
    order (the caller sorts globally by index — ADR-0003 determinism)."""
    groups_5m: dict[tuple[int, float, float], FastStructure] = {}
    groups_1h: dict[tuple[int, float, float], FastStructure] = {}
    contexts: dict[tuple[int, float, float], FastContext] = {}
    sims: list[tuple[int, FastSimulator, tuple[int, float, float]]] = []
    bound: list[tuple[FastSimulator, tuple[int, float, float]]] = []
    for index, n5, n1, mult, buf, r, ms in configs:
        k5 = (n5, mult, buf)
        k1 = (n1, mult, buf)
        if k5 not in groups_5m:
            groups_5m[k5] = FastStructure(n5, mult, buf)
        if k1 not in groups_1h:
            groups_1h[k1] = FastStructure(n1, mult, buf)
            contexts[k1] = FastContext()
        sim = FastSimulator(r, ms, groups_5m[k5], groups_1h[k1], log_trades=log_trades)
        sims.append((index, sim, k1))
        bound.append((sim, k5))

    for is_5m, warmup, ots, o, h, lo, c in rows:
        if not is_5m:
            for k1, structure in groups_1h.items():
                structure.update(o, h, lo, c)
                if not warmup:
                    contexts[k1].observe(structure.state_of())
            continue
        outs = {k5: structure.update(o, h, lo, c) for k5, structure in groups_5m.items()}
        for sim, k5 in bound:
            sim.on_5m(warmup, ots, o, h, lo, c, outs[k5])

    return [(index, sim.finalize(), contexts[k1], sim.trade_log) for index, sim, k1 in sims]


# -- multiprocessing plumbing (rows shipped once per worker) -----------------

_ROWS: list[tuple[bool, bool, int, float, float, float, float]] | None = None


def pool_init(rows: list[tuple[bool, bool, int, float, float, float, float]]) -> None:
    global _ROWS
    _ROWS = rows


def run_shard_pooled(
    configs: list[tuple[int, int, int, float, float, float, float]],
) -> list[tuple[int, FastMetrics, FastContext, object]]:
    assert _ROWS is not None, "pool_init was not called"
    return run_shard(_ROWS, configs)

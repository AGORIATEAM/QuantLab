"""EXP-20260902-002 (H3) float64 mirror (ADR-0003 perimeter).

FastH3Simulator is FastH2Simulator with the frozen stop change: stop
DISTANCE = max(wick extreme distance, k_stop x ATR_15m at the signal
close), no min_stop filter (redundant by construction), and the
stop_atr_dominated counter incremented when a position opens whose
distance came from the ATR term. With k_stop=0 it degenerates exactly to
FastH2Simulator at min_stop=0 (max(wick, 0) = wick) — the mini-CI
cross-checks that identity.

The decision timeframe is 15m: BAR_SECONDS=900 keeps the daily equity
day rule aligned with the Decimal side (close_time day).

run_shard_h3 replays MultiRow streams (timeframes [15m, 4h, 1d] in that
fixed index order) for a shard of the 96 frozen configurations; engines
shared per (stage, n, detector, mult, buffer), results returned by
configuration index (determinism)."""

from __future__ import annotations

from quantlab.research.fast.h1fast import (
    BEARISH,
    BULLISH,
    CHOCH,
    WICK,
    FastContext,
    FastMetrics,
    FastStructure,
)
from quantlab.research.fast.h2fast import FastH2Simulator

TF_15M, TF_4H, TF_1D = 0, 1, 2  # MultiRow timeframe indexes, frozen order
CONTEXT_N = {TF_4H: 5, TF_1D: 3}  # frozen: 4h n=5, 1d n=3

# (index, ctx_tf_idx, n_15m, det_is_atr, mult, buffer, r_target, k_stop)
H3Config = tuple[int, int, int, int, float, float, float, float]


class FastH3Simulator(FastH2Simulator):
    BAR_SECONDS = 900  # 15m decision candles

    def __init__(
        self,
        r_target: float,
        k_stop: float,
        structure_15m: FastStructure,
        structure_ctx: FastStructure,
        log_trades: bool = False,
    ) -> None:
        super().__init__(r_target, 0.0, structure_15m, structure_ctx, log_trades=log_trades)
        self.k_stop = k_stop
        self._pending_atr_dominated = False

    def _open_position(self, side: int, raw: float, stop: float, ots: int) -> None:
        had_position = self._position is not None
        super()._open_position(side, raw, stop, ots)
        if self._position is not None and not had_position and self._pending_atr_dominated:
            self.metrics.stop_atr_dominated += 1

    def _signals(self, events: list[tuple[int, int, float]], close: float) -> None:
        context_state = self.s1.state_of()
        for kind, direction, price in events:
            if kind == CHOCH and self._position is not None:
                against = direction == BEARISH if self._position.side > 0 else direction == BULLISH
                if against:
                    self._exit_pending = True
            if kind != WICK:
                continue
            if self._position is not None or self._entry_pending is not None:
                self.metrics.ignored_in_position += 1
                continue
            if context_state == BULLISH and direction == BEARISH:
                side = 1  # low swept while bullish -> long
            elif context_state == BEARISH and direction == BULLISH:
                side = -1  # high swept while bearish -> short
            else:
                continue
            wick_distance = (close - price) * side
            if wick_distance <= 0:
                continue
            atr = self.s5.atr.value
            if atr is None:
                continue  # unreachable post-ready, kept for symmetry with the slow side
            noise_floor = self.k_stop * atr
            distance = max(wick_distance, noise_floor)
            stop = close - side * distance
            self._pending_atr_dominated = noise_floor > wick_distance
            self._entry_pending = (side, stop)


def run_shard_h3(
    rows: list[tuple[int, bool, int, float, float, float, float]],
    configs: list[H3Config],
    log_trades: bool = False,
) -> list[tuple[int, FastMetrics, FastContext, object]]:
    groups_15m: dict[tuple, FastStructure] = {}
    groups_ctx: dict[tuple, FastStructure] = {}
    contexts: dict[tuple, FastContext] = {}
    sims: list[tuple[int, FastH3Simulator, tuple, tuple]] = []
    for index, ctx_idx, n15, det_atr, mult, buf, r, k in configs:
        k15 = (n15, det_atr, mult, buf)
        kc = (ctx_idx, det_atr, mult, buf)
        if k15 not in groups_15m:
            groups_15m[k15] = FastStructure(n15, mult, buf, filter_legs=bool(det_atr))
        if kc not in groups_ctx:
            groups_ctx[kc] = FastStructure(CONTEXT_N[ctx_idx], mult, buf, filter_legs=bool(det_atr))
            contexts[kc] = FastContext()
        sim = FastH3Simulator(r, k, groups_15m[k15], groups_ctx[kc], log_trades=log_trades)
        sims.append((index, sim, k15, kc))

    for tf_idx, warmup, ots, o, h, lo, c in rows:
        if tf_idx != TF_15M:
            for kc, structure in groups_ctx.items():
                if kc[0] != tf_idx:
                    continue
                structure.update(o, h, lo, c)
                if not warmup:
                    contexts[kc].observe(structure.state_of())
            continue
        outs = {k15: structure.update(o, h, lo, c) for k15, structure in groups_15m.items()}
        for _index, sim, k15, _kc in sims:
            sim.on_5m(warmup, ots, o, h, lo, c, outs[k15])

    return [(index, sim.finalize(), contexts[kc], sim.trade_log) for index, sim, _k15, kc in sims]


# -- multiprocessing plumbing ------------------------------------------------

_ROWS: list[tuple[int, bool, int, float, float, float, float]] | None = None


def pool_init_h3(rows: list[tuple[int, bool, int, float, float, float, float]]) -> None:
    global _ROWS
    _ROWS = rows


def run_shard_h3_pooled(
    configs: list[H3Config],
) -> list[tuple[int, FastMetrics, FastContext, object]]:
    assert _ROWS is not None, "pool_init_h3 was not called"
    return run_shard_h3(_ROWS, configs)

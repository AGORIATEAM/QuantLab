"""EXP-20260902-001 (H2) float64 mirror (ADR-0003 perimeter).

FastH2Simulator overrides only the signal reading of FastSimulator —
exactly like H2Simulator overrides H1Simulator on the Decimal side:
entry on a WICK_BREAK against the slow context (recovery close intrinsic),
stop at the wick extreme, min_stop vs ATR_5m at signal close, same CHoCH
exit, fills, sizing and metrics.

run_shard_h2 replays extracted MultiRow streams (timeframes
[5m, 1h, 4h] in that fixed index order) for a shard of the 288 frozen
configurations; engines are shared per (stage, n, detector, mult, buffer)
group and results are returned by configuration index (determinism)."""

from __future__ import annotations

from quantlab.research.fast.h1fast import (
    BEARISH,
    BULLISH,
    CHOCH,
    WICK,
    FastContext,
    FastMetrics,
    FastSimulator,
    FastStructure,
)

TF_5M, TF_1H, TF_4H = 0, 1, 2  # MultiRow timeframe indexes, frozen order
CONTEXT_N = {TF_1H: 8, TF_4H: 5}  # frozen: 1h n=8, 4h n=5

# (index, ctx_tf_idx, n_5m, det_is_atr, mult, buffer, r_target, min_stop)
H2Config = tuple[int, int, int, int, float, float, float, float]


class FastH2Simulator(FastSimulator):
    def _signals(self, events: list[tuple[int, int, float, float]], close: float) -> None:
        context_state = self.s1.state_of()
        for kind, direction, price, _level in events:
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
            stop = price  # the wick extreme
            distance = (close - stop) * side
            if distance <= 0:
                continue
            atr = self.s5.atr.value
            if atr is not None and distance < self.min_stop_atr * atr:
                self.metrics.skipped_min_stop += 1
                continue
            self._entry_pending = (side, stop)


def run_shard_h2(
    rows: list[tuple[int, bool, int, float, float, float, float]],
    configs: list[H2Config],
    log_trades: bool = False,
) -> list[tuple[int, FastMetrics, FastContext, object]]:
    groups_5m: dict[tuple, FastStructure] = {}
    groups_ctx: dict[tuple, FastStructure] = {}
    contexts: dict[tuple, FastContext] = {}
    sims: list[tuple[int, FastH2Simulator, tuple, tuple]] = []
    for index, ctx_idx, n5, det_atr, mult, buf, r, ms in configs:
        k5 = (n5, det_atr, mult, buf)
        kc = (ctx_idx, det_atr, mult, buf)
        if k5 not in groups_5m:
            groups_5m[k5] = FastStructure(n5, mult, buf, filter_legs=bool(det_atr))
        if kc not in groups_ctx:
            groups_ctx[kc] = FastStructure(CONTEXT_N[ctx_idx], mult, buf, filter_legs=bool(det_atr))
            contexts[kc] = FastContext()
        sim = FastH2Simulator(r, ms, groups_5m[k5], groups_ctx[kc], log_trades=log_trades)
        sims.append((index, sim, k5, kc))

    for tf_idx, warmup, ots, o, h, lo, c in rows:
        if tf_idx != TF_5M:
            for kc, structure in groups_ctx.items():
                if kc[0] != tf_idx:
                    continue
                structure.update(o, h, lo, c)
                if not warmup:
                    contexts[kc].observe(structure.state_of())
            continue
        outs = {k5: structure.update(o, h, lo, c) for k5, structure in groups_5m.items()}
        for _index, sim, k5, _kc in sims:
            sim.on_5m(warmup, ots, o, h, lo, c, outs[k5])

    return [(index, sim.finalize(), contexts[kc], sim.trade_log) for index, sim, _k5, kc in sims]


# -- multiprocessing plumbing ------------------------------------------------

_ROWS: list[tuple[int, bool, int, float, float, float, float]] | None = None


def pool_init_h2(rows: list[tuple[int, bool, int, float, float, float, float]]) -> None:
    global _ROWS
    _ROWS = rows


def run_shard_h2_pooled(
    configs: list[H2Config],
) -> list[tuple[int, FastMetrics, FastContext, object]]:
    assert _ROWS is not None, "pool_init_h2 was not called"
    return run_shard_h2(_ROWS, configs)

"""EXP-20260902-003 (H4) float64 mirror (ADR-0003 perimeter).

FastH4Simulator trades exactly like FastH3Simulator (identical
population) and labels each trade at the signal close against the J-1
daily profile carried by the extraction rows (extract_rows_multi_h4 —
levels converted Decimal -> float ONCE, freshness decided on the Decimal
side). Bucket indices mirror quantlab.profile.BUCKETS order; the primary
subset is long x SOUS_VAL union short x SUR_VAH; primary_ignored counts
swallowed would-be-primary sweeps (frozen addition to the IS report).

Equivalence adds LABEL PARITY: label_log (side, bucket) per closed trade
compared exactly against the Decimal reference, plus per-(side, bucket)
counters and primary_ignored."""

from __future__ import annotations

from dataclasses import dataclass

from quantlab.research.fast.extract import MultiRowH4, ProfTuple
from quantlab.research.fast.h1fast import (
    BEARISH,
    BULLISH,
    CHOCH,
    WICK,
    FastContext,
    FastMetrics,
    FastStructure,
)
from quantlab.research.fast.h3fast import CONTEXT_N, TF_15M, FastH3Simulator, H3Config

NO_PROFILE, HORS_PLAGE, POC_ZONE, SOUS_VAL, SUR_VAH, DANS_VALEUR = range(6)
POC_ZONE_ATR = 0.25
N_BUCKETS = 6


def classify_f(level: float, atr: float, prof: ProfTuple | None) -> int:
    """float mirror of quantlab.profile.classify_level — same priority
    order; the no_profile/stale branch is already folded into prof=None."""
    if prof is None:
        return NO_PROFILE
    poc, vah, val, day_low, day_high = prof
    if level > day_high or level < day_low:
        return HORS_PLAGE
    if abs(level - poc) <= POC_ZONE_ATR * atr:
        return POC_ZONE
    if level <= val:
        return SOUS_VAL
    if level >= vah:
        return SUR_VAH
    return DANS_VALEUR


def is_primary_f(side: int, bucket: int) -> bool:
    return (side > 0 and bucket == SOUS_VAL) or (side < 0 and bucket == SUR_VAH)


@dataclass
class FastBucketStats:
    trades: int = 0
    wins: int = 0
    sum_r: float = 0.0
    pos_r: float = 0.0
    neg_r: float = 0.0
    sum_cost_r: float = 0.0
    sum_stop_pct: float = 0.0
    dominated: int = 0


class FastH4Simulator(FastH3Simulator):
    def __init__(
        self,
        r_target: float,
        k_stop: float,
        structure_15m: FastStructure,
        structure_ctx: FastStructure,
        log_trades: bool = False,
    ) -> None:
        super().__init__(r_target, k_stop, structure_15m, structure_ctx, log_trades=log_trades)
        self.prof: ProfTuple | None = None  # set by the shard loop per 15m candle
        self.bucket_stats = {
            (side, bucket): FastBucketStats() for side in (1, -1) for bucket in range(N_BUCKETS)
        }
        self.primary_ignored = 0
        self.label_log: list[tuple[int, int]] = []
        self._pending_label = 0
        self._open_label = 0
        self._open_dominated = False

    def _open_position(self, side: int, raw: float, stop: float, ots: int) -> None:
        had_position = self._position is not None
        super()._open_position(side, raw, stop, ots)
        if self._position is not None and not had_position:
            self._open_label = self._pending_label
            self._open_dominated = self._pending_atr_dominated

    def _close_position(self, raw: float) -> None:
        position = self._position
        assert position is not None
        m = self.metrics
        before = (m.sum_r, m.sum_cost_r, m.sum_stop_pct, m.wins)
        super()._close_position(raw)
        stats = self.bucket_stats[(1 if position.side > 0 else -1, self._open_label)]
        stats.trades += 1
        stats.wins += m.wins - before[3]
        r_delta = m.sum_r - before[0]
        stats.sum_r += r_delta
        if r_delta > 0:
            stats.pos_r += r_delta
        else:
            stats.neg_r += -r_delta
        stats.sum_cost_r += m.sum_cost_r - before[1]
        stats.sum_stop_pct += m.sum_stop_pct - before[2]
        if self._open_dominated:
            stats.dominated += 1
        self.label_log.append((position.side, self._open_label))

    def _signals(self, events: list[tuple[int, int, float, float]], close: float) -> None:
        context_state = self.s1.state_of()
        for kind, direction, price, level in events:
            if kind == CHOCH and self._position is not None:
                against = direction == BEARISH if self._position.side > 0 else direction == BULLISH
                if against:
                    self._exit_pending = True
            if kind != WICK:
                continue
            if context_state == BULLISH and direction == BEARISH:
                side = 1  # low swept while bullish -> long
            elif context_state == BEARISH and direction == BULLISH:
                side = -1  # high swept while bearish -> short
            else:
                side = 0
            if self._position is not None or self._entry_pending is not None:
                self.metrics.ignored_in_position += 1
                if side != 0:
                    atr = self.s5.atr.value
                    if atr is not None and is_primary_f(side, classify_f(level, atr, self.prof)):
                        self.primary_ignored += 1
                continue
            if side == 0:
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
            self._pending_label = classify_f(level, atr, self.prof)
            self._pending_atr_dominated = noise_floor > wick_distance
            self._entry_pending = (side, stop)


H4Result = tuple[
    int,
    FastMetrics,
    FastContext,
    object,  # trade_log
    dict[tuple[int, int], FastBucketStats],
    int,  # primary_ignored
    list[tuple[int, int]],  # label_log
]


def run_shard_h4(
    rows: list[MultiRowH4],
    configs: list[H3Config],
    log_trades: bool = False,
) -> list[H4Result]:
    groups_15m: dict[tuple, FastStructure] = {}
    groups_ctx: dict[tuple, FastStructure] = {}
    contexts: dict[tuple, FastContext] = {}
    sims: list[tuple[int, FastH4Simulator, tuple, tuple]] = []
    for index, ctx_idx, n15, det_atr, mult, buf, r, k in configs:
        k15 = (n15, det_atr, mult, buf)
        kc = (ctx_idx, det_atr, mult, buf)
        if k15 not in groups_15m:
            groups_15m[k15] = FastStructure(n15, mult, buf, filter_legs=bool(det_atr))
        if kc not in groups_ctx:
            groups_ctx[kc] = FastStructure(CONTEXT_N[ctx_idx], mult, buf, filter_legs=bool(det_atr))
            contexts[kc] = FastContext()
        sim = FastH4Simulator(r, k, groups_15m[k15], groups_ctx[kc], log_trades=log_trades)
        sims.append((index, sim, k15, kc))

    for tf_idx, warmup, ots, o, h, lo, c, prof in rows:
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
            sim.prof = prof
            sim.on_5m(warmup, ots, o, h, lo, c, outs[k15])

    return [
        (
            index,
            sim.finalize(),
            contexts[kc],
            sim.trade_log,
            sim.bucket_stats,
            sim.primary_ignored,
            sim.label_log,
        )
        for index, sim, _k15, kc in sims
    ]


# -- multiprocessing plumbing ------------------------------------------------

_ROWS: list[MultiRowH4] | None = None


def pool_init_h4(rows: list[MultiRowH4]) -> None:
    global _ROWS
    _ROWS = rows


def run_shard_h4_pooled(configs: list[H3Config]) -> list[H4Result]:
    assert _ROWS is not None, "pool_init_h4 was not called"
    return run_shard_h4(_ROWS, configs)

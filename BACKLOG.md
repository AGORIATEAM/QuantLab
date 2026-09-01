# Backlog

Items deliberately deferred, with their origin. Roadmap phases live in
docs/25; this file tracks cross-cutting debts decided during reviews.

## Phase 2

- **Common fill model** (from the T7bis friction report): every Phase 2
  engine will need the same signal→next-open fill automaton that
  `quantlab/research/baseline.py` hand-rolls. Extract a shared simulator
  (research/execution layer, NOT the replay engine) and fix its conventions
  once, notably: **trade counting** (T7bis counts the final liquidation as a
  trade), partial fills, sizing. Comparisons across experiments are only
  valid at identical fill model.
- **verify-at-startup optimization** (from T7): the full per-series hash
  verification at replay startup is the Phase 1 rule. Any fast path
  (count-only, cached verdicts) is a Phase 2 decision to be made against the
  recorded benchmarks (12 series: verify ~121s / stream ~419s).

## Data (revision conditions from ADR-0001)

- `dataset_lineage` table: first derived dataset (aggregation/correction).
- Parquet export + object storage: when volume degrades search queries or
  V2 data (trades, order book) lands.
- Raw REST archiving: mandatory before any new import if a CANDLE_MISMATCH
  divergence between re-downloads is ever observed.

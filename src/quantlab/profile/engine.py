"""Volume Profile Engine — docs/07, minimal Hyp-4 perimeter (POC/VAH/VAL).

TRANSPOSITION (documented per plan, user-validated 2026-09-02): the classic
Market Profile session (ASIA/LONDON/NEW_YORK) does not exist on a continuous
crypto market. QuantLab uses the UTC DAY as the analytical session
(docs/07 SS26-27): one profile per UTC day, built from the day's 15m OHLCV
candles. Volume is distributed by the UNIFORM method (SS11) — each candle's
volume spread over [low, high] proportionally to bin overlap — so the data
quality is CANDLE_ESTIMATED (SS6), recorded on every profile. Single venue by
construction (the dataset is single-venue; SS60).

Frozen definitions (arbitrations A-E, user-validated):
- bins: Fixed Number of Rows (SS9), default 100 over [day_low, day_high];
  degenerate candle (high == low) puts its full volume in its bin.
- POC: argmax bin volume; tie -> the LOWEST-price bin (SS14). The POC price
  is the midpoint of that bin.
- Value Area (SS15-16, default 70%): greedy expansion from the POC, one bin
  at a time — the larger of the two adjacent bins wins, tie -> the LOWER
  side — stopping as soon as the included volume reaches the target share.
  VAH = upper edge of the highest included bin, VAL = lower edge of the
  lowest included bin. A zero-volume day degenerates to VA = the POC bin.
- Availability (SS69-71): the profile of day J is finalized when the first
  candle of a LATER day arrives and carries available_at = J+1 00:00 UTC;
  the developing profile is never readable. previous() returns the last
  FINAL profile — during day J, that is J-1 (or older after a full-day
  venue gap: the `day` field is the caller's staleness check).
- Warm-up: previous() is None until one full day has been finalized;
  warm-up candles do feed the accumulator (the replay lookback provides
  the prior day, as with the structure engine seeding).

Out of the Hyp-4 perimeter, deferred (BACKLOG): HVN/LVN, developing POC,
events, persistence, rolling/anchored/composite profiles.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

from quantlab.data.replay import ReplayEvent, SeriesKey

ENGINE_VERSION = "0.1.0"
DATA_QUALITY = "CANDLE_ESTIMATED"  # docs/07 SS6 — OHLCV uniform distribution
ZERO = Decimal(0)


@dataclass(frozen=True)
class ProfileConfig:
    bins: int = 100
    value_area: Decimal = Decimal("0.70")
    expected_count: int = 96  # 15m candles per UTC day, coverage reference

    @property
    def config_version(self) -> str:
        canonical = f"qlvp-v1|{self.bins}|{self.value_area}|{self.expected_count}"
        return hashlib.sha256(canonical.encode()).hexdigest()[:12]


@dataclass(frozen=True)
class VolumeProfile:
    day: date
    poc: Decimal  # midpoint of the POC bin
    vah: Decimal  # upper edge of the highest value-area bin
    val: Decimal  # lower edge of the lowest value-area bin
    day_low: Decimal
    day_high: Decimal
    total_volume: Decimal
    candle_count: int
    expected_count: int
    data_quality: str
    available_at: datetime  # J+1 00:00 UTC — backtests must respect it (SS71)
    engine_version: str
    config_version: str


@dataclass
class _DayAccumulator:
    day: date
    candles: list[tuple[Decimal, Decimal, Decimal]] = field(default_factory=list)  # (lo, hi, vol)


class VolumeProfileEngine:
    """One finalized daily profile per series, batch-computed at day rollover
    (96 candles a day: incremental bookkeeping would buy nothing, SS66)."""

    def __init__(self, config: ProfileConfig | None = None) -> None:
        self.config = config or ProfileConfig()
        self._current: dict[SeriesKey, _DayAccumulator] = {}
        self._previous: dict[SeriesKey, VolumeProfile] = {}

    def on_event(self, event: ReplayEvent) -> None:
        key = event.series
        candle = event.candle
        day = candle.open_time.astimezone(UTC).date()
        current = self._current.get(key)
        if current is not None and current.day != day:
            self._previous[key] = self._finalize(current)
            current = None
        if current is None:
            current = _DayAccumulator(day)
            self._current[key] = current
        current.candles.append((candle.low, candle.high, candle.volume))

    def previous(self, key: SeriesKey) -> VolumeProfile | None:
        """The last FINAL profile — never the developing one (SS69-70)."""
        return self._previous.get(key)

    def _finalize(self, acc: _DayAccumulator) -> VolumeProfile:
        day_low = min(lo for lo, _hi, _v in acc.candles)
        day_high = max(hi for _lo, hi, _v in acc.candles)
        bins = self.config.bins
        volumes = [ZERO] * bins
        width = (day_high - day_low) / bins

        def bin_index(price: Decimal) -> int:
            if width == 0:
                return 0
            return min(int((price - day_low) / width), bins - 1)

        for lo, hi, vol in acc.candles:
            if hi == lo or width == 0:
                volumes[bin_index(lo)] += vol
                continue
            first, last = bin_index(lo), bin_index(hi)
            span = hi - lo
            for i in range(first, last + 1):
                bin_lo = day_low + width * i
                bin_hi = day_high if i == bins - 1 else bin_lo + width
                overlap = min(hi, bin_hi) - max(lo, bin_lo)
                if overlap > 0:
                    volumes[i] += vol * overlap / span

        total = sum(volumes, ZERO)
        poc_idx = max(range(bins), key=lambda i: (volumes[i], -i))  # tie -> lowest bin
        # greedy value-area expansion from the POC (tie -> lower side)
        lo_idx = hi_idx = poc_idx
        included = volumes[poc_idx]
        target = total * self.config.value_area
        while included < target and (lo_idx > 0 or hi_idx < bins - 1):
            below = volumes[lo_idx - 1] if lo_idx > 0 else None
            above = volumes[hi_idx + 1] if hi_idx < bins - 1 else None
            if above is None or (below is not None and below >= above):
                lo_idx -= 1
                included += volumes[lo_idx]
            else:
                hi_idx += 1
                included += volumes[hi_idx]

        available_at = datetime.combine(acc.day + timedelta(days=1), time(0, tzinfo=UTC))
        return VolumeProfile(
            day=acc.day,
            poc=day_low + width * poc_idx + width / 2 if width else day_low,
            vah=day_high if hi_idx == bins - 1 else day_low + width * (hi_idx + 1),
            val=day_low + width * lo_idx,
            day_low=day_low,
            day_high=day_high,
            total_volume=total,
            candle_count=len(acc.candles),
            expected_count=self.config.expected_count,
            data_quality=DATA_QUALITY,
            available_at=available_at,
            engine_version=ENGINE_VERSION,
            config_version=self.config.config_version,
        )

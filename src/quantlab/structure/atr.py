"""Wilder ATR (docs/06 §11, §19-B). Deterministic, warm-up aware, Decimal."""

from __future__ import annotations

from decimal import Decimal

from quantlab.domain.models import Candle


class WilderAtr:
    """True range smoothed à la Wilder: the first ATR is the simple average
    of the first `period` true ranges, then
    atr = (atr * (period - 1) + tr) / period. `value` is None until warm."""

    def __init__(self, period: int = 14) -> None:
        if period < 1:
            raise ValueError("ATR period must be >= 1")
        self.period = period
        self._previous_close: Decimal | None = None
        self._warmup_trs: list[Decimal] = []
        self._value: Decimal | None = None

    @property
    def value(self) -> Decimal | None:
        return self._value

    @property
    def ready(self) -> bool:
        return self._value is not None

    def update(self, candle: Candle) -> Decimal | None:
        if self._previous_close is None:
            tr = candle.high - candle.low
        else:
            tr = max(
                candle.high - candle.low,
                abs(candle.high - self._previous_close),
                abs(candle.low - self._previous_close),
            )
        self._previous_close = candle.close
        if self._value is None:
            self._warmup_trs.append(tr)
            if len(self._warmup_trs) == self.period:
                self._value = sum(self._warmup_trs, Decimal(0)) / self.period
        else:
            self._value = (self._value * (self.period - 1) + tr) / self.period
        return self._value

"""Typed domain models mirroring the initial schema (23-Database-Schema).

Frozen (immutable) pydantic models; Decimal for financial values; aware UTC
timestamps only. Invalid states are rejected at construction (20-Engineering-
Principles §27: make invalid states difficult).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from quantlab.core.timeutils import require_utc


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True)


class AssetClass(StrEnum):
    CRYPTO = "crypto"
    FOREX = "forex"
    COMMODITY = "commodity"
    EQUITY = "equity"
    INDEX = "index"


class InstrumentStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELISTED = "delisted"


class Timeframe(StrEnum):
    M1 = "1m"
    M3 = "3m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"


class Asset(FrozenModel):
    asset_id: uuid.UUID
    symbol: str
    asset_class: AssetClass
    base_asset: str | None = None
    quote_asset: str | None = None
    price_precision: int | None = None
    quantity_precision: int | None = None
    tick_size: Decimal | None = None
    lot_size: Decimal | None = None
    is_active: bool = True


class Venue(FrozenModel):
    venue_id: uuid.UUID
    code: str
    name: str
    venue_type: str
    is_active: bool = True


class Instrument(FrozenModel):
    instrument_id: uuid.UUID
    venue_id: uuid.UUID
    asset_id: uuid.UUID | None
    venue_symbol: str
    instrument_type: str
    tick_size: Decimal
    lot_size: Decimal
    min_quantity: Decimal | None = None
    min_notional: Decimal | None = None
    status: InstrumentStatus = InstrumentStatus.ACTIVE


class Candle(FrozenModel):
    """OHLCV candle. Integrity invariants enforced here AND in the database."""

    candle_id: uuid.UUID
    instrument_id: uuid.UUID
    timeframe: Timeframe
    open_time: datetime
    close_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    trade_count: int | None = None
    source: str
    data_version: str | None = None

    @field_validator("open_time", "close_time")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return require_utc(value)

    @model_validator(mode="after")
    def _integrity(self) -> Candle:
        if self.close_time <= self.open_time:
            raise ValueError("close_time must be strictly after open_time")
        if not (self.high >= self.open and self.high >= self.close and self.high >= self.low):
            raise ValueError("high must be >= open, close and low")
        if not (self.low <= self.open and self.low <= self.close):
            raise ValueError("low must be <= open and close")
        if self.volume < 0:
            raise ValueError("volume must be >= 0")
        return self


class QualitySeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class QualityCode(StrEnum):
    """Data quality anomaly codes (03-Data-Engine §17-§20, Roadmap §26)."""

    GAP = "GAP"
    KNOWN_VENUE_GAP = "KNOWN_VENUE_GAP"
    DUPLICATE_SKIPPED = "DUPLICATE_SKIPPED"
    CANDLE_MISMATCH = "CANDLE_MISMATCH"
    OUT_OF_ORDER = "OUT_OF_ORDER"
    STALE_DATA = "STALE_DATA"
    INVALID_CANDLE = "INVALID_CANDLE"


class DataQualityEvent(FrozenModel):
    """A detected data anomaly (23-Database-Schema §19). Never blocks the
    pipeline silently: suspicious data is recorded here, not destroyed."""

    event_id: uuid.UUID
    dataset_type: str
    instrument_id: uuid.UUID | None
    severity: QualitySeverity
    code: QualityCode
    event_time: datetime
    details: dict[str, Any] | None = None
    resolved_at: datetime | None = None

    @field_validator("event_time")
    @classmethod
    def _utc_event_time(cls, value: datetime) -> datetime:
        return require_utc(value)

    @field_validator("resolved_at")
    @classmethod
    def _utc_resolved_at(cls, value: datetime | None) -> datetime | None:
        return None if value is None else require_utc(value)


class StrategyStatus(StrEnum):
    DRAFT = "draft"
    RESEARCH = "research"
    PAPER = "paper"
    PRODUCTION = "production"
    RETIRED = "retired"


class Strategy(FrozenModel):
    strategy_id: uuid.UUID
    strategy_code: str
    name: str
    description: str | None = None
    status: StrategyStatus = StrategyStatus.DRAFT
    current_version: str | None = None
    owner: str | None = None

"""Typed raw payloads from the Binance public REST API.

Frozen dataclasses with strict manual parsing, not pydantic: at this trust
boundary prices MUST arrive as JSON strings and go straight to Decimal —
pydantic's lenient coercion would silently accept floats (docs/17 §24, §171).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from quantlab.data.errors import MalformedPayloadError

KLINE_FIELD_COUNT = 12  # documented shape; index 11 is an "ignore" field


def _expect_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise MalformedPayloadError(
            f"field {field!r} must be an integer, got {type(value).__name__}"
        )
    return value


def _expect_str(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise MalformedPayloadError(f"field {field!r} must be a string, got {type(value).__name__}")
    return value


def _expect_decimal_str(value: object, field: str) -> Decimal:
    raw = _expect_str(value, field)
    try:
        return Decimal(raw)
    except InvalidOperation as exc:
        raise MalformedPayloadError(f"field {field!r} is not a valid decimal: {raw!r}") from exc


@dataclass(frozen=True)
class RawKline:
    """One row of GET /api/v3/klines, exactly as the venue sent it."""

    open_time_ms: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    close_time_ms: int
    quote_volume: Decimal
    trade_count: int
    taker_buy_base_volume: Decimal
    taker_buy_quote_volume: Decimal

    @classmethod
    def from_api(cls, row: object) -> RawKline:
        if not isinstance(row, list) or len(row) != KLINE_FIELD_COUNT:
            raise MalformedPayloadError(
                f"kline row must be a {KLINE_FIELD_COUNT}-element array, got {row!r}"
            )
        return cls(
            open_time_ms=_expect_int(row[0], "open_time"),
            open=_expect_decimal_str(row[1], "open"),
            high=_expect_decimal_str(row[2], "high"),
            low=_expect_decimal_str(row[3], "low"),
            close=_expect_decimal_str(row[4], "close"),
            volume=_expect_decimal_str(row[5], "volume"),
            close_time_ms=_expect_int(row[6], "close_time"),
            quote_volume=_expect_decimal_str(row[7], "quote_volume"),
            trade_count=_expect_int(row[8], "trade_count"),
            taker_buy_base_volume=_expect_decimal_str(row[9], "taker_buy_base_volume"),
            taker_buy_quote_volume=_expect_decimal_str(row[10], "taker_buy_quote_volume"),
        )


@dataclass(frozen=True)
class SymbolInfo:
    """Instrument metadata from GET /api/v3/exchangeInfo — the venue is the
    source of truth for tick/lot sizes (seed values are placeholders)."""

    symbol: str
    status: str
    base_asset: str
    quote_asset: str
    base_asset_precision: int
    quote_asset_precision: int
    tick_size: Decimal
    step_size: Decimal
    min_quantity: Decimal
    min_notional: Decimal | None

    @classmethod
    def from_api(cls, payload: object) -> SymbolInfo:
        if not isinstance(payload, dict):
            raise MalformedPayloadError(f"symbol entry must be an object, got {payload!r}")
        filters: dict[str, dict[str, object]] = {}
        raw_filters = payload.get("filters")
        if not isinstance(raw_filters, list):
            raise MalformedPayloadError("symbol entry has no 'filters' array")
        for f in raw_filters:
            if isinstance(f, dict) and isinstance(f.get("filterType"), str):
                filters[f["filterType"]] = f

        price_filter = filters.get("PRICE_FILTER")
        lot_size = filters.get("LOT_SIZE")
        if price_filter is None or lot_size is None:
            raise MalformedPayloadError("symbol entry misses PRICE_FILTER or LOT_SIZE filter")
        # NOTIONAL is the current name; MIN_NOTIONAL existed on older payloads.
        notional = filters.get("NOTIONAL") or filters.get("MIN_NOTIONAL")

        return cls(
            symbol=_expect_str(payload.get("symbol"), "symbol"),
            status=_expect_str(payload.get("status"), "status"),
            base_asset=_expect_str(payload.get("baseAsset"), "baseAsset"),
            quote_asset=_expect_str(payload.get("quoteAsset"), "quoteAsset"),
            base_asset_precision=_expect_int(
                payload.get("baseAssetPrecision"), "baseAssetPrecision"
            ),
            quote_asset_precision=_expect_int(
                payload.get("quoteAssetPrecision"), "quoteAssetPrecision"
            ),
            tick_size=_expect_decimal_str(price_filter.get("tickSize"), "tickSize"),
            step_size=_expect_decimal_str(lot_size.get("stepSize"), "stepSize"),
            min_quantity=_expect_decimal_str(lot_size.get("minQty"), "minQty"),
            min_notional=(
                None
                if notional is None
                else _expect_decimal_str(notional.get("minNotional"), "minNotional")
            ),
        )

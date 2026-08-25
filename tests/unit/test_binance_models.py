"""Strict parsing of Binance raw payloads: strings→Decimal, never float."""

from decimal import Decimal

import pytest
from fixtures_binance import SYMBOL_ENTRY, VALID_KLINE_ROW

from quantlab.data.binance.models import RawKline, SymbolInfo
from quantlab.data.errors import MalformedPayloadError


def test_valid_kline_row_parses_to_exact_decimals() -> None:
    kline = RawKline.from_api(VALID_KLINE_ROW)
    assert kline.open_time_ms == 1756166400000
    assert kline.close_time_ms == 1756166459999
    assert kline.trade_count == 1234
    # str comparison: the venue's exact decimal representation is preserved
    assert str(kline.open) == "111544.83000000"
    assert str(kline.volume) == "5.70120000"
    assert kline.high == Decimal("111608.00000000")


def test_price_sent_as_number_is_rejected() -> None:
    row = list(VALID_KLINE_ROW)
    row[1] = 111544.83  # float would silently lose precision — must be refused
    with pytest.raises(MalformedPayloadError, match="'open'"):
        RawKline.from_api(row)


def test_wrong_field_count_is_rejected() -> None:
    with pytest.raises(MalformedPayloadError, match="12-element"):
        RawKline.from_api(VALID_KLINE_ROW[:11])


def test_non_list_row_is_rejected() -> None:
    with pytest.raises(MalformedPayloadError):
        RawKline.from_api({"open": "1"})


def test_boolean_is_not_an_integer() -> None:
    row = list(VALID_KLINE_ROW)
    row[8] = True
    with pytest.raises(MalformedPayloadError, match="'trade_count'"):
        RawKline.from_api(row)


def test_garbage_decimal_string_is_rejected() -> None:
    row = list(VALID_KLINE_ROW)
    row[2] = "not-a-number"
    with pytest.raises(MalformedPayloadError, match="'high'"):
        RawKline.from_api(row)


def test_symbol_info_parses_filters_exactly() -> None:
    info = SymbolInfo.from_api(SYMBOL_ENTRY)
    assert info.symbol == "BTCUSDT"
    assert info.base_asset == "BTC"
    assert info.quote_asset == "USDT"
    assert str(info.tick_size) == "0.01000000"
    assert str(info.step_size) == "0.00001000"
    assert str(info.min_quantity) == "0.00001000"
    assert info.min_notional is not None and str(info.min_notional) == "5.00000000"


def test_symbol_info_accepts_legacy_min_notional_filter() -> None:
    entry = {
        **SYMBOL_ENTRY,
        "filters": [
            SYMBOL_ENTRY["filters"][0],
            SYMBOL_ENTRY["filters"][1],
            {"filterType": "MIN_NOTIONAL", "minNotional": "10.00000000"},
        ],
    }
    info = SymbolInfo.from_api(entry)
    assert info.min_notional == Decimal("10.00000000")


def test_symbol_info_without_notional_filter_is_allowed() -> None:
    entry = {**SYMBOL_ENTRY, "filters": SYMBOL_ENTRY["filters"][:2]}
    assert SymbolInfo.from_api(entry).min_notional is None


def test_symbol_info_missing_lot_size_is_rejected() -> None:
    entry = {**SYMBOL_ENTRY, "filters": [SYMBOL_ENTRY["filters"][0]]}
    with pytest.raises(MalformedPayloadError, match="LOT_SIZE"):
        SymbolInfo.from_api(entry)

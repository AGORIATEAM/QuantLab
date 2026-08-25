"""Real-shaped Binance public API payload excerpts (public data, no secrets).

Small, explicit, deterministic (docs/17 §76) — shared by the connector tests.
"""

VALID_KLINE_ROW = [
    1756166400000,
    "111544.83000000",
    "111608.00000000",
    "111544.82000000",
    "111585.19000000",
    "5.70120000",
    1756166459999,
    "636135.98244430",
    1234,
    "3.11530000",
    "347565.90714300",
    "0",
]

SECOND_KLINE_ROW = [
    1756166460000,
    "111585.19000000",
    "111650.00000000",
    "111570.01000000",
    "111612.35000000",
    "8.11000000",
    1756166519999,
    "905176.20000000",
    2201,
    "4.00000000",
    "446450.00000000",
    "0",
]

KLINES_PAYLOAD = [VALID_KLINE_ROW, SECOND_KLINE_ROW]

SYMBOL_ENTRY = {
    "symbol": "BTCUSDT",
    "status": "TRADING",
    "baseAsset": "BTC",
    "baseAssetPrecision": 8,
    "quoteAsset": "USDT",
    "quoteAssetPrecision": 8,
    "filters": [
        {
            "filterType": "PRICE_FILTER",
            "minPrice": "0.01000000",
            "maxPrice": "1000000.00000000",
            "tickSize": "0.01000000",
        },
        {
            "filterType": "LOT_SIZE",
            "minQty": "0.00001000",
            "maxQty": "9000.00000000",
            "stepSize": "0.00001000",
        },
        {"filterType": "NOTIONAL", "minNotional": "5.00000000", "applyMinToMarket": True},
    ],
}

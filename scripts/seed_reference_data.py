"""Seed reference data for the validated V1 scope: BTC/USDT and ETH/USDT (spot, Binance).

Idempotent: safe to run repeatedly (ON CONFLICT DO NOTHING).
Tick/lot sizes are bootstrap placeholders; the Phase 1 Data Engine must refresh
them from the venue's exchange-info endpoint (source of truth: the venue).
"""

from __future__ import annotations

import os
import sys

import psycopg
from uuid6 import uuid7


def main() -> None:
    url = os.environ.get("QUANTLAB_DATABASE_URL")
    if not url:
        print("QUANTLAB_DATABASE_URL is not set", file=sys.stderr)
        raise SystemExit(2)
    with psycopg.connect(url) as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO venues (venue_id, code, name, venue_type)
            VALUES (%s, 'BINANCE', 'Binance', 'crypto_exchange')
            ON CONFLICT (code) DO NOTHING
            """,
            (uuid7(),),
        )
        cur.execute("SELECT venue_id FROM venues WHERE code = 'BINANCE'")
        row = cur.fetchone()
        assert row is not None
        venue_id = row[0]

        pairs = [
            ("BTC/USDT", "BTC", "USDT", "BTCUSDT"),
            ("ETH/USDT", "ETH", "USDT", "ETHUSDT"),
        ]
        for symbol, base, quote, venue_symbol in pairs:
            cur.execute(
                """
                INSERT INTO assets (asset_id, symbol, asset_class, base_asset, quote_asset)
                VALUES (%s, %s, 'crypto', %s, %s)
                ON CONFLICT (symbol) DO NOTHING
                """,
                (uuid7(), symbol, base, quote),
            )
            cur.execute("SELECT asset_id FROM assets WHERE symbol = %s", (symbol,))
            arow = cur.fetchone()
            assert arow is not None
            cur.execute(
                """
                INSERT INTO instruments (
                    instrument_id, venue_id, asset_id, venue_symbol,
                    instrument_type, tick_size, lot_size, status
                )
                VALUES (%s, %s, %s, %s, 'spot', 0.01, 0.00001, 'active')
                ON CONFLICT (venue_id, venue_symbol) DO NOTHING
                """,
                (uuid7(), venue_id, arow[0], venue_symbol),
            )
        conn.commit()
    print("Reference data seeded (BINANCE, BTC/USDT, ETH/USDT).")


if __name__ == "__main__":
    main()

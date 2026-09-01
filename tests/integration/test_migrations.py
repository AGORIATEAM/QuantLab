"""Migration runner behavior against a real database."""

from __future__ import annotations

import os
import subprocess
import sys
import uuid
from pathlib import Path

import psycopg
import pytest

pytestmark = pytest.mark.integration

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_all_migrations_applied_and_recorded(database_url: str) -> None:
    with psycopg.connect(database_url) as conn, conn.cursor() as cur:
        cur.execute("SELECT filename FROM schema_migrations ORDER BY filename")
        applied = [r[0] for r in cur.fetchall()]
    on_disk = sorted(p.name for p in (REPO_ROOT / "migrations").glob("*.sql"))
    assert applied == on_disk


def test_rerunning_migrations_is_a_noop(database_url: str) -> None:
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "migrate.py")],
        env={**os.environ, "QUANTLAB_DATABASE_URL": database_url},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "apply" not in result.stdout


def test_candle_integrity_checks_enforced_at_database_level(
    database_url: str, btc_instrument_id: uuid.UUID
) -> None:
    """The OHLC CHECK constraints of 0001 are the last defense against direct
    SQL writes (the domain model rejects invalid candles before repos). T10
    audit found them untested — one representative violation per family."""
    base = """
        INSERT INTO candles (
            candle_id, instrument_id, timeframe, open_time, close_time,
            open, high, low, close, volume, source
        )
        VALUES (%s, %s, '1h', '2033-01-01T00:00Z', {close_time},
                {open}, {high}, {low}, {close}, {volume}, 'binance')
    """
    violations = {
        "candle_high_ge_close": {
            "close_time": "'2033-01-01T01:00Z'",
            "open": 100,
            "high": 101,
            "low": 99,
            "close": 150,
            "volume": 1,
        },
        "candle_low_le_open": {
            "close_time": "'2033-01-01T01:00Z'",
            "open": 100,
            "high": 200,
            "low": 150,
            "close": 160,
            "volume": 1,
        },
        "candle_volume_ge_0": {
            "close_time": "'2033-01-01T01:00Z'",
            "open": 100,
            "high": 101,
            "low": 99,
            "close": 100,
            "volume": -1,
        },
        "candle_time_order": {
            "close_time": "'2032-12-31T23:00Z'",
            "open": 100,
            "high": 101,
            "low": 99,
            "close": 100,
            "volume": 1,
        },
    }
    with psycopg.connect(database_url) as conn, conn.cursor() as cur:
        for constraint, values in violations.items():
            with pytest.raises(psycopg.errors.CheckViolation, match=constraint):
                cur.execute(base.format(**values), (uuid.uuid4(), btc_instrument_id))
            conn.rollback()


def test_audit_events_table_is_append_only(database_url: str) -> None:
    with psycopg.connect(database_url) as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO audit_events (
                audit_event_id, actor_type, actor_id, action, resource_type, result
            )
            VALUES (%s, 'service', 'integration-test', 'APPEND_ONLY_CHECK', 'test', 'success')
            """,
            (uuid.uuid4(),),
        )
        conn.commit()
        with pytest.raises(psycopg.errors.RaiseException):
            cur.execute("DELETE FROM audit_events WHERE action = 'APPEND_ONLY_CHECK'")

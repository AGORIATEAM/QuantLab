"""Integration test harness: real PostgreSQL against the committed migrations.

A dedicated `quantlab_test` database is dropped, recreated, migrated
(scripts/migrate.py) and seeded (scripts/seed_reference_data.py) once per
session, so tests always exercise the exact schema and reference data a fresh
environment would get. Test data never touches quantlab_dev (04-Storage §51).

If no local PostgreSQL is reachable (`make db-up`), every integration test is
skipped — CI runs them with a service container (Phase 1, T10).
"""

from __future__ import annotations

import os
import subprocess
import sys
import uuid
from pathlib import Path

import psycopg
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ADMIN_URL_DEFAULT = "postgresql://quantlab:quantlab_local_only@localhost:5432/quantlab_dev"
TEST_DB_NAME = "quantlab_test"


def _admin_url() -> str:
    return os.environ.get("QUANTLAB_TEST_ADMIN_URL", ADMIN_URL_DEFAULT)


def _test_url() -> str:
    base, _, _ = _admin_url().rpartition("/")
    return f"{base}/{TEST_DB_NAME}"


def _run_script(name: str, database_url: str) -> None:
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / name)],
        env={**os.environ, "QUANTLAB_DATABASE_URL": database_url},
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(f"scripts/{name} failed:\n{result.stdout}\n{result.stderr}")


@pytest.fixture(scope="session")
def database_url() -> str:
    """URL of a freshly migrated + seeded quantlab_test database."""
    try:
        admin = psycopg.connect(_admin_url(), connect_timeout=2)
    except psycopg.OperationalError as exc:
        if os.environ.get("CI"):
            # In CI a missing database is a broken pipeline, never a silent skip.
            pytest.fail(f"CI requires PostgreSQL but it is unreachable: {exc}")
        pytest.skip("PostgreSQL not reachable — run `make db-up` to enable integration tests")
    admin.autocommit = True
    with admin.cursor() as cur:
        cur.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME} WITH (FORCE)")
        cur.execute(f"CREATE DATABASE {TEST_DB_NAME}")
    admin.close()

    url = _test_url()
    _run_script("migrate.py", url)
    _run_script("seed_reference_data.py", url)
    return url


@pytest.fixture(scope="session")
def btc_instrument_id(database_url: str) -> uuid.UUID:
    """instrument_id of the seeded BTCUSDT spot instrument on Binance."""
    with psycopg.connect(database_url) as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT i.instrument_id
            FROM instruments i JOIN venues v ON v.venue_id = i.venue_id
            WHERE v.code = 'BINANCE' AND i.venue_symbol = 'BTCUSDT'
            """
        )
        row = cur.fetchone()
    assert row is not None, "seed_reference_data.py did not create BTCUSDT on BINANCE"
    return row[0]

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

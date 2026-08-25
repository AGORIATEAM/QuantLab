"""Deterministic SQL migration runner.

Applies migrations/*.sql in lexical order, once each, recording filename and
content hash in schema_migrations. A migration whose content changed after
being applied causes a hard failure (immutability of applied migrations).
"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

import psycopg

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"

SCHEMA_MIGRATIONS = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    filename TEXT PRIMARY KEY,
    content_sha256 TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


def database_url() -> str:
    url = os.environ.get("QUANTLAB_DATABASE_URL")
    if not url:
        print("QUANTLAB_DATABASE_URL is not set", file=sys.stderr)
        raise SystemExit(2)
    return url


def main() -> None:
    files = sorted(p for p in MIGRATIONS_DIR.glob("*.sql"))
    if not files:
        print("No migrations found.")
        return
    with psycopg.connect(database_url()) as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_MIGRATIONS)
            conn.commit()
            for path in files:
                content = path.read_text(encoding="utf-8")
                digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
                cur.execute(
                    "SELECT content_sha256 FROM schema_migrations WHERE filename = %s",
                    (path.name,),
                )
                row = cur.fetchone()
                if row is not None:
                    if row[0] != digest:
                        print(
                            f"FATAL: {path.name} changed after being applied "
                            f"(recorded {row[0][:12]}…, current {digest[:12]}…)",
                            file=sys.stderr,
                        )
                        raise SystemExit(1)
                    print(f"skip  {path.name} (already applied)")
                    continue
                cur.execute(content)
                cur.execute(
                    "INSERT INTO schema_migrations (filename, content_sha256) VALUES (%s, %s)",
                    (path.name, digest),
                )
                conn.commit()
                print(f"apply {path.name}")
    print("Migrations up to date.")


if __name__ == "__main__":
    main()

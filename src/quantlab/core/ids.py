"""Identifiers (23-Database-Schema §5): UUIDv7 primary IDs + readable business IDs."""

from __future__ import annotations

import secrets
import uuid

from uuid6 import uuid7

from quantlab.core.timeutils import utc_now


def new_id() -> uuid.UUID:
    """Time-ordered UUIDv7 — sortable, index-friendly."""
    return uuid7()


def new_business_id(prefix: str) -> str:
    """Readable business ID, e.g. EXP-20260825-a3f9.

    Uniqueness is enforced by the database, not by this generator.
    """
    if not prefix.isalpha() or not prefix.isupper():
        raise ValueError("prefix must be uppercase letters, e.g. 'EXP', 'STR'")
    stamp = utc_now().strftime("%Y%m%d")
    suffix = secrets.token_hex(2)
    return f"{prefix}-{stamp}-{suffix}"

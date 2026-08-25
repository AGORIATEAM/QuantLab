"""Time handling (20-Engineering-Principles §31-§32): UTC internally, always aware."""

from __future__ import annotations

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Current time as an aware UTC datetime."""
    return datetime.now(UTC)


def require_utc(value: datetime, field: str = "timestamp") -> datetime:
    """Reject naive datetimes; normalize aware datetimes to UTC."""
    if value.tzinfo is None:
        raise ValueError(f"{field} must be timezone-aware (UTC). Naive datetimes are forbidden.")
    return value.astimezone(UTC)

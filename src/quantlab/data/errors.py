"""Connector error taxonomy (17-AI-Development-Protocol §40).

Callers can react per failure mode instead of catching bare exceptions.
"""

from __future__ import annotations


class ConnectorError(Exception):
    """Base class for market data connector failures."""


class MalformedPayloadError(ConnectorError):
    """The venue response does not match its documented schema. Never silently
    coerced: malformed data is rejected at the boundary (docs/17 §171)."""


class RetryExhaustedError(ConnectorError):
    """Transient failures (timeouts, 5xx, 429) persisted beyond the bounded
    retry budget."""


class IPBannedError(ConnectorError):
    """HTTP 418: the venue banned this IP for rate-limit abuse. Hard stop —
    retrying makes the ban longer."""

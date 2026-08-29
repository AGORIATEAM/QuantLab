"""Structured JSON logging with request/correlation IDs (Roadmap §14-§15).

Every log line is a JSON object carrying timestamp (UTC), level, event, and any
bound context (request_id, correlation_id, environment).
"""

from __future__ import annotations

import logging

import structlog

# Chatty third-party loggers capped at WARNING so DEBUG/INFO runs stay
# readable: httpx logs every request, httpcore every socket operation.
_NOISY_THIRD_PARTY_LOGGERS = ("httpx", "httpcore")


def configure_logging(level: str = "INFO") -> None:
    """Configure structlog for JSON output. Idempotent."""
    logging.basicConfig(level=level, format="%(message)s")
    for name in _NOISY_THIRD_PARTY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelNamesMapping()[level.upper()]
        ),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)


def bind_request_context(request_id: str, correlation_id: str) -> None:
    """Bind IDs so every subsequent log line in this context carries them."""
    structlog.contextvars.bind_contextvars(request_id=request_id, correlation_id=correlation_id)


def clear_request_context() -> None:
    structlog.contextvars.clear_contextvars()

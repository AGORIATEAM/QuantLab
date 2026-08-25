"""Audit events (23-Database-Schema §73-§75): append-only, everything traceable."""

from __future__ import annotations

import uuid
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict


class ActorType(StrEnum):
    HUMAN = "human"
    SERVICE = "service"
    AI_AGENT = "ai_agent"


class AuditResult(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    DENIED = "denied"


class AuditEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    audit_event_id: uuid.UUID
    actor_type: ActorType
    actor_id: str
    action: str
    resource_type: str
    resource_id: str | None
    environment: str | None
    request_id: str | None
    correlation_id: str | None
    result: AuditResult
    metadata: dict[str, Any] | None = None

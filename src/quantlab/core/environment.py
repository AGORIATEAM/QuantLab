"""Environment model (19-Deployment-Guide §3-§6).

Six environments, with an explicit guard preventing accidental production use.
"""

from __future__ import annotations

from enum import StrEnum


class Environment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    RESEARCH = "research"
    PAPER = "paper"
    SHADOW = "shadow"
    PRODUCTION = "production"


class ProductionGuardError(RuntimeError):
    """Raised when production is selected without the explicit guard."""


def guard_environment(environment: Environment, allow_production: bool) -> Environment:
    """Refuse PRODUCTION unless explicitly allowed (Environment Guard).

    Fail closed: in doubt, the system must not run against production.
    """
    if environment is Environment.PRODUCTION and not allow_production:
        raise ProductionGuardError(
            "Environment 'production' requires QUANTLAB_ALLOW_PRODUCTION=true. "
            "This guard exists so production is always a deliberate choice."
        )
    return environment

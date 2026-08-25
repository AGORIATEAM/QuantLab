"""Versioned, layered configuration (Roadmap §12, 19-Deployment-Guide §33-§35).

Layers: configs/base.yaml ← configs/<environment>.yaml ← environment variables
(QUANTLAB_ prefix). Secrets never live in YAML files — only references via env.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Self

import yaml
from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict

from quantlab.core.environment import Environment, guard_environment


class Settings(BaseSettings):
    """Values injected from the process environment (.env in local dev)."""

    model_config = SettingsConfigDict(env_prefix="QUANTLAB_", env_file=".env", extra="ignore")

    environment: Environment = Environment.DEVELOPMENT
    database_url: str = ""
    allow_production: bool = False


class AppConfig(BaseModel):
    """Merged, validated configuration for one environment."""

    model_config = ConfigDict(frozen=True)

    config_version: str
    environment: Environment
    log_level: str
    database_url: str
    trading_enabled: bool

    @classmethod
    def load(cls, settings: Settings | None = None, configs_dir: Path | None = None) -> Self:
        settings = settings or Settings()
        environment = guard_environment(settings.environment, settings.allow_production)
        directory = configs_dir or Path(__file__).resolve().parents[3] / "configs"

        merged: dict[str, Any] = {}
        for name in ("base.yaml", f"{environment.value}.yaml"):
            path = directory / name
            if path.exists():
                loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                if not isinstance(loaded, dict):
                    raise ValueError(f"{path} must contain a YAML mapping")
                merged.update(loaded)

        return cls(
            config_version=str(merged.get("config_version", "0")),
            environment=environment,
            log_level=str(merged.get("log_level", "INFO")),
            database_url=settings.database_url,
            trading_enabled=bool(merged.get("trading_enabled", False)),
        )

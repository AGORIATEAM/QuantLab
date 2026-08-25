from pathlib import Path

from quantlab.core.config import AppConfig, Settings
from quantlab.core.environment import Environment


def test_layered_config(tmp_path: Path) -> None:
    (tmp_path / "base.yaml").write_text("config_version: '1'\nlog_level: INFO\n")
    (tmp_path / "test.yaml").write_text("log_level: WARNING\n")
    settings = Settings(environment=Environment.TEST, database_url="postgresql://x", _env_file=None)
    config = AppConfig.load(settings=settings, configs_dir=tmp_path)
    assert config.log_level == "WARNING"  # env layer overrides base
    assert config.config_version == "1"  # inherited from base
    assert config.trading_enabled is False  # safe default


def test_repo_configs_all_disable_trading() -> None:
    """No committed configuration may enable trading in Phase 0."""
    configs_dir = Path(__file__).resolve().parents[2] / "configs"
    for env in Environment:
        settings = Settings(environment=env, allow_production=True, _env_file=None)
        config = AppConfig.load(settings=settings, configs_dir=configs_dir)
        assert config.trading_enabled is False, f"trading must be disabled in {env}"

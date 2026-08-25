import pytest

from quantlab.core.environment import Environment, ProductionGuardError, guard_environment


def test_non_production_passes() -> None:
    assert guard_environment(Environment.RESEARCH, False) is Environment.RESEARCH


def test_production_blocked_by_default() -> None:
    with pytest.raises(ProductionGuardError):
        guard_environment(Environment.PRODUCTION, False)


def test_production_requires_explicit_flag() -> None:
    assert guard_environment(Environment.PRODUCTION, True) is Environment.PRODUCTION

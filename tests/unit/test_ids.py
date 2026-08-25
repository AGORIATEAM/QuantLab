import pytest

from quantlab.core.ids import new_business_id, new_id


def test_uuid7_are_time_ordered() -> None:
    first, second = new_id(), new_id()
    assert first < second


def test_business_id_format() -> None:
    value = new_business_id("EXP")
    parts = value.split("-")
    assert parts[0] == "EXP"
    assert len(parts[1]) == 8
    assert len(parts[2]) == 4


def test_business_id_rejects_bad_prefix() -> None:
    with pytest.raises(ValueError):
        new_business_id("exp1")

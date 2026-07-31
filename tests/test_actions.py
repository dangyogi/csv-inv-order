# test_actions.py

import pytest
from unittest.mock import Mock

from csv_inv_order.actions import check_fudge_factors


@pytest.fixture
def row_screen(fields):
    return Mock(fields=fields)

@pytest.fixture
def fields(rest):
    fields = (("table_size", "8"),) + rest
    return [make_field(attrs) for attrs in fields]

def make_field(attrs):
    ans = Mock()
    ans.configure_mock(name=attrs[0], text=attrs[1])
    return ans

@pytest.mark.parametrize("rest", [
    (("served_fudge", "1.3"), ("consumed_fudge", "0.9")),
    (("consumed_fudge", "0.9"), ("served_fudge", "1.3")),
])
def test_check_fudge_factors_pass(row_screen, rest):
    assert len(row_screen.fields) == 3
    assert row_screen.fields[0].name == "table_size"
    assert check_fudge_factors(row_screen) is None

@pytest.mark.parametrize("rest", [
    (("served_fudge", "0.8"), ("consumed_fudge", "0.9")),
    (("consumed_fudge", "0.9"), ("served_fudge", "1.5")),
])
def test_check_fudge_factors_bad_served(row_screen, rest):
    assert check_fudge_factors(row_screen).startswith("served_fudge must be between ")

@pytest.mark.parametrize("rest", [
    (("served_fudge", None), ("consumed_fudge", "0.9")),
    (("consumed_fudge", "0.9"), ("served_fudge", None)),
])
def test_check_fudge_factors_empty_served(row_screen, rest):
    assert check_fudge_factors(row_screen).startswith("You must set served_fudge between ")

@pytest.mark.parametrize("rest", [
    (("served_fudge", "1.3"), ("consumed_fudge", "0.5")),
    (("consumed_fudge", "1.3"), ("served_fudge", "1.3")),
])
def test_check_fudge_factors_bad_consumed(row_screen, rest):
    assert check_fudge_factors(row_screen).startswith("consumed_fudge must be between ")

@pytest.mark.parametrize("rest", [
    (("served_fudge", "1.3"), ("consumed_fudge", None)),
    (("consumed_fudge", None), ("served_fudge", "1.3")),
])
def test_check_fudge_factors_empty_consumed(row_screen, rest):
    assert check_fudge_factors(row_screen).startswith("You must set consumed_fudge between ")

@pytest.mark.parametrize("rest", [
    (("served_fudge", "1.3"), ),
    (("consumed_fudge", "0.9"), ),
    (),
])
def test_check_fudge_factors_missing(row_screen, rest):
    with pytest.raises(AssertionError):
        check_fudge_factors(row_screen)

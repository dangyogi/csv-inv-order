# test_calc_consumed.py

from unittest.mock import Mock
import pytest

from csv_inv_order import calc_consumed


@pytest.fixture
def app_setup(mocker):
    def set_params(table_size=8, uncertainty_pct=0.2):
        mocker.patch("csv_inv_order.calc_consumed.Months.last_month").return_value.table_size = table_size
        def call2_returning(q, fn, start, convert_fn):
            fn(uncertainty_pct)
        mocker.patch("csv_inv_order.calc_consumed.calc_consumed2")
        return Mock(screen=Mock(ask_question=call2_returning))
    return set_params

def test_app1(app_setup):
    fn = Mock()
    app = app_setup()
    app.screen.ask_question("q", fn, "1", convert_fn=int)
    fn.assert_called_once_with(0.2)
    assert calc_consumed.Months.last_month().table_size == 8

def test_app2(app_setup):
    fn = Mock()
    app = app_setup(4, 0.3)
    app.screen.ask_question("q", fn, "1", convert_fn=int)
    fn.assert_called_once_with(0.3)
    assert calc_consumed.Months.last_month().table_size == 4

@pytest.mark.parametrize("table_size", (4, 12))
def test_calc_consumed_ok_table_size(app_setup, table_size):
    step = None
    app = app_setup(table_size)
    calc_consumed.calc_consumed(step, app)

@pytest.mark.parametrize("table_size", (3, 13))
def test_calc_consumed_bad_table_size(app_setup, table_size):
    step = None
    app = app_setup(table_size)
    with pytest.raises(ValueError) as exc_info:
        calc_consumed.calc_consumed(step, app)
    exc_obj = exc_info.value
    assert str(exc_obj).endswith(" must be 4-12")

@pytest.mark.parametrize("uncertainty_pct", (0.05, 0.1, 0.50))
def test_calc_consumed_ok_uncertainty_pct(app_setup, uncertainty_pct):
    step = None
    app = app_setup(uncertainty_pct=uncertainty_pct)
    calc_consumed.calc_consumed(step, app)

@pytest.mark.parametrize("uncertainty_pct", (0.04, 0.51))
def test_calc_consumed_bad_uncertainty_pct(app_setup, uncertainty_pct):
    step = None
    app = app_setup(uncertainty_pct=uncertainty_pct)
    with pytest.raises(ValueError) as exc_info:
        calc_consumed.calc_consumed(step, app)
    exc_obj = exc_info.value
    assert str(exc_obj).endswith(" must be 0.05-0.50")

# test_tables.py

# the only thing to test in tables.py is Months

import pytest

from csv_inv_order.database import *


@pytest.fixture(scope="module", autouse=True)
def create_database():
    Months.clear()
    Months.insert(month=1, year=2025, num_at_meeting=10, staff_at_breakfast=20, tickets_claimed=40)
    Months.insert(month=1, year=2026, num_at_meeting=12, served_fudge=1.1, consumed_fudge=0.5, table_size=8,
                  staff_at_breakfast=10, tickets_claimed=60)
    Months.insert(month=2, year=2026)


def test_inc_dec_month():
    assert Months.inc_month(2026, 11) == (2026, 12)
    assert Months.inc_month(2026, 12) == (2027, 1)
    assert Months.inc_month(2026, 4) == (2026, 5)
    assert Months.dec_month(2026, 1) == (2025, 12)
    assert Months.dec_month(2026, 12) == (2026, 11)
    assert Months.dec_month(2026, 11) == (2026, 10)

def test_last_month():
    assert Months.last_month().month_str == "Feb '26"

def test_avg_num_at_meeting():
    assert Months.avg_num_at_meeting(1) == 11
    assert Months.avg_num_at_meeting(2) is None
    
def test_avg_staff_at_breakfast():
    assert Months.avg_staff_at_breakfast(1) == 15
    assert Months.avg_staff_at_breakfast(2) is None
    
def test_avg_tickets_claimed():
    assert Months.avg_tickets_claimed(1) == 50
    assert Months.avg_tickets_claimed(2) is None

def test_avg_meals_served():
    assert Months.avg_meals_served(1) == 65
    assert Months.avg_meals_served(2) is None
    
def test_meals_planned():
    assert Months.meals_planned(1, 1.1) == 70
    assert Months.meals_planned(2, 1.1) is None
    

# test_months.py

import pytest

from csv_inv_order.database import *


@pytest.fixture(scope="module", autouse=True)
def create_database():
    Months.clear()
    Months.insert(month=1, year=2025, staff_at_breakfast=20, tickets_claimed=40)
    Months.insert(month=1, year=2026, served_fudge=1.1, consumed_fudge=0.5, table_size=8,
                  staff_at_breakfast=10, tickets_claimed=60)
    Months.insert(month=2, year=2026)

@pytest.fixture
def cur_month():
    return Months[2026, 1]

def test_prev_month():
    assert Months[2026, 1].prev_month == (2025, 12)
    assert Months[2026, 2].prev_month == (2026, 1)

def test_meals_served():
    assert Months[2026, 1].meals_served == 70
    assert Months[2026, 2].meals_served is None

def test_meeting_date():
    assert Months[2026, 1].meeting_date == date(2026, 1, 6)
    assert Months[2026, 2].meeting_date == date(2026, 2, 3)

def test_breakfast_date():
    assert Months[2026, 1].breakfast_date == date(2026, 1, 10)
    assert Months[2026, 2].breakfast_date == date(2026, 2, 14)

def test_avg_staff_at_breakfast():
    assert Months[2026, 1].avg_staff_at_breakfast == 15

def test_avg_tickets_claimed():
    assert Months[2026, 1].avg_tickets_claimed == 50

def test_avg_meals_served():
    assert Months[2026, 1].avg_meals_served == 65

def test_meals_planned():
    # only tickets_claimed is fudged
    # avg_staff is 15, avg_tickets is 50, served_fudge is 1.1
    assert Months[2026, 1].meals_planned == 70

def test_num_tables():
    # avg_tickets is 50, served_fudge is 1.1, so seating 55
    assert Months[2026, 1].num_tables == 7
    assert Months[2026, 2].num_tables is None


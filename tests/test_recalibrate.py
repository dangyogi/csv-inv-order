# test_recalibrate.py

import pytest

from csv_inv_order import recalibrate
from csv_inv_order.database import *


def mk_date(month, day, year=2025):
    return date(year, month, day)

def mk_day(day):
    return date(2025, 1, day)

@pytest.fixture(scope="module", autouse=True)
def create_Months():
    Months.clear()
    for month in 1,2,3,4,11:  # breakfast_days: 11, 8, 8, 12, 8
        Months.insert(month=month, year=2025, staff_at_breakfast=20, tickets_claimed=month)
    for month in 1,2,3,4,11,12:
        Months.insert(month=month, year=2024, staff_at_breakfast=10, tickets_claimed=month)

@pytest.fixture(scope="module", autouse=True)
def create_Items():
    r'''Loads item, pkg_size
    '''
    Products.clear()
    Products.insert(item="Eggs", name="Eggs", price=2.00, pkg_size=24, supplier="Sams", supplier_id=1,
                    skip_fk_check=True)
    Products.insert(item="Milk", name="Milk", price=3.00, pkg_size=64, supplier="Sams", supplier_id=1,
                    skip_fk_check=True)
    Products.insert(item="Salt", name="Salt", price=4.00, pkg_size=10, supplier="Sams", supplier_id=1,
                    skip_fk_check=True)
    Products.insert(item="Bogus", name="Bogus", price=5.00, pkg_size=15, supplier="Sams", supplier_id=1,
                    skip_fk_check=True)
    Items.clear()
    Items.insert(item="Eggs", unit="eq", perishable=True, num_per_serving=2.2, supplier="Sams", supplier_id=1)
    Items.insert(item="Milk", unit="oz", perishable=False, num_per_meal=32, supplier="Sams", supplier_id=1)
    Items.insert(item="Salt", unit="oz", perishable=False, num_per_table=1, supplier="Sams", supplier_id=1)
    Items.insert(item="Bogus", unit="foo", perishable=False, supplier="Sams", supplier_id=1)

@pytest.fixture(scope="module", autouse=True)
def create_Inventory(create_Items):
    r'''Loads item, date=Jan 1, 26, code, num_pkgs=0, num_units
    '''
    Inventory.clear()
    for day, code, num_units \
     in [   # Milk: num_units * 10
        (1, "purchased", 4),
        (2, "estimate", 5),
        (3, "count", 6),
        (4, "used", 2),
        (5, "count", 3),
        (6, "purchased", 7),
    ]:
        Inventory.insert(item="Eggs", date=mk_day(day), code=code, num_units=num_units)
        Inventory.insert(item="Milk", date=mk_day(day), code=code, num_units=num_units * 10)


@pytest.mark.parametrize("date, month", [
    (mk_date(11, 7), (2025, 4)),   # 11/2025 breakfast on the 8th
    (mk_date(11, 8), (2025, 11)),
    (mk_date(11, 9), (2025, 11)),
    (mk_date(1, 11), (2025, 1)),    # 1/2025 breakfast on the 11th
    (mk_date(1, 10), (2024, 12)),
])
def test_get_breakfast(date, month):
    assert recalibrate.get_breakfast(date).key() == month

def test_get_counts():
    counts = list(recalibrate.get_counts())
    assert counts == [("Eggs", mk_day(3), 6, mk_day(5), 5), ("Milk", mk_day(3), 60, mk_day(5), 50)]

@pytest.mark.parametrize("item, exp_head, exp_tail", [
    ("Eggs", "Eggs: stored num_per_serving=2.2", "per_serving=12.00"),
    ("Milk", "Milk: stored num_per_meal=32", "per_meal=6.00"),
    ("Salt", "Salt: stored num_per_table=1", "per_table=8.00"),
    ("Bogus", "Bogus: no stored consumption set", None),
])
def test_get_line1(item, exp_head, exp_tail):
    head, tail_fn = recalibrate.get_line1(item)
    assert head == exp_head
    assert tail_fn(24, 2, 3, 4) == exp_tail  # tail_fn(consumed, total_served, total_tables, total_months)

def tail_fn(consumed, served, tables, months):
    return f"{consumed=}, {served=}, {tables=}, {months=}"

def test_process_counts0():
    counts = ()
    tail, lines = recalibrate.process_counts(tail_fn, counts, 10)
    assert tail == "consumed=0, served=0, tables=0, months=0"
    assert lines == []

@pytest.mark.parametrize("counts, exp_tail, exp_lines", [
    ([("Eggs", mk_date(2,15), 200, mk_date(11, 15), 100)],
     "consumed=100, served=78, tables=10, months=3",
     [["  item='Eggs', start=Feb 15, 25, end=Nov 15, 25, served=78, months=3, consumed=100.00",
       "consumed=100, served=78, tables=10, months=3"]]),

    ([("Eggs", mk_date(4,15,2024), 20, mk_date(2, 15), 10)],
     "consumed=10, served=86, tables=12, months=4",
     [["  item='Eggs', start=Apr 15, 24, end=Feb 15, 25, served=86, months=4, consumed=10.00",
       "consumed=10, served=86, tables=12, months=4"]]),

    ([("Eggs", mk_date(2,15), 200, mk_date(11, 15), 100),
      ("Eggs", mk_date(4,15,2024), 20, mk_date(2, 15), 10)],
     "consumed=110, served=164, tables=22, months=7",
     [["  item='Eggs', start=Feb 15, 25, end=Nov 15, 25, served=78, months=3, consumed=100.00",
       "consumed=100, served=78, tables=10, months=3"],
      ["  item='Eggs', start=Apr 15, 24, end=Feb 15, 25, served=86, months=4, consumed=10.00",
       "consumed=10, served=86, tables=12, months=4"]]),
])
def test_process_counts1(counts, exp_tail, exp_lines):
    tail, lines = recalibrate.process_counts(tail_fn, counts, 10)
    assert tail == exp_tail
    assert lines == exp_lines


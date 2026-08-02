# test_create_orders.py

r'''Includes test_items tests to share create_database fixture.
'''

from decimal import Decimal
import pytest

from csv_inv_order.database import *
from csv_inv_order.create_orders import create_month_stats, create_order_stats, create_orders


@pytest.fixture(scope="module", autouse=True)
def create_database():
    Items.clear()
    items = [("Eggs", "ea", True, 24), ("Butter", "chip", False, 200), ("Milk", "oz", True, 64),
             ("Nonstick Spray", "can", False, 2)]
    for item, unit, perishable, pkg_size in items:
        Items.insert(item=item, unit=unit, perishable=perishable, supplier="Sams", supplier_id=1, skip_fk_check=True)
        Products.insert(item=item, supplier="Sams", supplier_id=1, name=item, price=Decimal("1.0"), pkg_size=pkg_size)
    Items["Eggs"].num_per_serving = 2.2
    Items["Butter"].num_per_table = 12.0
    Items["Butter"].num_per_serving = 1.0
    Items["Milk"].num_per_meal = 32.0
    Items["Nonstick Spray"].num_per_meal = 1.0
    Items["Nonstick Spray"].num_per_serving = 0.01

    Inventory.clear()
    Eggs = [("count", 10), ("purchased", 24), ("consumed", 14)]                          # 20
    for code, num_units in Eggs:
        Inventory.insert(date='Jan 01, 26', item="Eggs", code=code, num_units=num_units)
    Inventory[-1].uncertainty = 5

    Butter  = [("estimate", 50), ("purchased", 24), ("consumed", 14), ("used", 10)]      # 50
    for code, num_units in Butter:
        Inventory.insert(date='Jan 01, 26', item="Butter", code=code, num_units=num_units)
    Inventory[-4].uncertainty = 5
    Inventory[-2].uncertainty = 10
    Inventory[-1].uncertainty = 7

    Milk = [("count", 64), ("consumed", 32)]                                             # 32
    for code, num_units in Milk:
        Inventory.insert(date='Jan 01, 26', item="Milk", code=code, num_units=num_units)
    Inventory[-1].uncertainty = 10

    Spray = [("count", 0.5), ("consumed", 0.4)]                                          # 0.1
    for code, num_units in Spray:
        Inventory.insert(date='Jan 01, 26', item="Nonstick Spray", code=code, num_units=num_units)
    Inventory[-1].uncertainty = 0.5

    Months.clear()
    Months.insert(month=1, year=2026, served_fudge=1.1, consumed_fudge=0.5, table_size=8,
                  staff_at_breakfast=10, tickets_claimed=173)                     # 200 w/fudge, 92 consumed
                                                                                  # 24 tables
    Months.insert(month=2, year=2026, staff_at_breakfast=10, tickets_claimed=82)  # 100 w/fudge
                                                                                  # 12 tables

@pytest.fixture
def cur_month():
    return Months[2026, 1]

@pytest.fixture
def month_stats():
    class attrs:
        def __init__(self, **attrs):
            self._keys = []
            for key, value in attrs.items():
                self._keys.append(key)
                setattr(self, key, value)
    return attrs(month=1, next_month=2, avg_served1=183, avg_served2=92, served_fudge=1.1,
                 meals_planned1=200, meals_planned2=100, num_tables1=24, num_tables2=12, table_size=8,
                 consumed_fudge=0.5)


# item tests:

def test_inventory():
    rows = list(Inventory.values())
    assert rows[0].item == 'Eggs'
    assert rows[0].code == 'count'
    assert rows[-1].item == 'Nonstick Spray'
    assert rows[-1].code == 'consumed'

def test_months():
    rows = list(Months.values())
    assert rows[0].month == 1
    assert rows[0].year == 2026
    assert rows[0].served_fudge == 1.1
    assert rows[0].table_size == 8
    assert rows[0].meals_planned == 200
    assert rows[1].month == 2
    assert rows[1].year == 2026
    assert rows[1].table_size == 8
    assert Months.meals_planned(2, 1.1) == 100

def test_in_stock():
    assert Items["Eggs"].in_stock() == (20, 5)
    assert Items["Butter"].in_stock() == (50, 22)
    assert Items["Milk"].in_stock() == (32, 10)
    assert Items["Nonstick Spray"].in_stock() == (0, 0.5)

def test_calc_needed():
    assert Items["Eggs"].calc_needed(200, 24) == 440
    assert Items["Butter"].calc_needed(200, 24) == 288
    assert Items["Milk"].calc_needed(200, 24) == 32
    assert Items["Nonstick Spray"].calc_needed(200, 24) == 1

def test_consumed():
    assert Items["Eggs"].consumed(92, 24) == 202
    assert Items["Butter"].consumed(92, 24) == 92
    assert Items["Milk"].consumed(92, 24) == 32
    assert Items["Nonstick Spray"].consumed(92, 24) == 1


# create_order tests:

def test_create_month_stats(cur_month, month_stats):
    ms = create_month_stats(cur_month)
    for attr in month_stats._keys:
        assert getattr(ms, attr) == getattr(month_stats, attr)

@pytest.mark.parametrize("item, attr, value", [
    ("Eggs", "item", "Eggs"),
    ("Eggs", "unit", "ea"),
    ("Eggs", "pkg_size", 24),
    ("Eggs", "perishable", True),
    ("Eggs", "inv_units", 20),
    ("Eggs", "uncertainty", 5),
    ("Eggs", "min_needed1", 440),
    ("Eggs", "min1", 18),
    ("Eggs", "max1", 18),
    ("Eggs", "consumed1", None),
    ("Eggs", "min_next", None),
    ("Eggs", "min_needed2", None),
    ("Eggs", "min2", None),
    ("Eggs", "max2", None),
    ("Eggs", "order", 18),

    ("Butter", "item", "Butter"),
    ("Butter", "unit", "chip"),
    ("Butter", "pkg_size", 200),
    ("Butter", "perishable", False),
    ("Butter", "inv_units", 50),
    ("Butter", "uncertainty", 22),
    ("Butter", "min_needed1", 288),
    ("Butter", "min1", 2),
    ("Butter", "max1", 2),
    ("Butter", "consumed1", 92),
    ("Butter", "min_next", 144),
    ("Butter", "min_needed2", 236),
    ("Butter", "min2", 2),
    ("Butter", "max2", 1),
    ("Butter", "order", 2),

    ("Milk", "item", "Milk"),
    ("Milk", "unit", "oz"),
    ("Milk", "pkg_size", 64),
    ("Milk", "perishable", True),
    ("Milk", "inv_units", 32),
    ("Milk", "uncertainty", 10),
    ("Milk", "min_needed1", 32),
    ("Milk", "min1", 1),
    ("Milk", "max1", 0),
    ("Milk", "consumed1", None),
    ("Milk", "min_next", None),
    ("Milk", "min_needed2", None),
    ("Milk", "min2", None),
    ("Milk", "max2", None),
    ("Milk", "order", 1),

    ("Nonstick Spray", "item", "Nonstick Spray"),
    ("Nonstick Spray", "unit", "can"),
    ("Nonstick Spray", "pkg_size", 2),
    ("Nonstick Spray", "perishable", False),
    ("Nonstick Spray", "inv_units", 0),
    ("Nonstick Spray", "uncertainty", 0.5),
    ("Nonstick Spray", "min_needed1", 1),
    ("Nonstick Spray", "min1", 1),
    ("Nonstick Spray", "max1", 1),
    ("Nonstick Spray", "consumed1", 1),
    ("Nonstick Spray", "min_next", 1),
    ("Nonstick Spray", "min_needed2", 2),
    ("Nonstick Spray", "min2", 1),
    ("Nonstick Spray", "max2", 1),
    ("Nonstick Spray", "order", 1),

])
def test_create_order_stats(cur_month, month_stats, item, attr, value):
    order_stats = create_order_stats(Items[item], cur_month, month_stats, override=True)
    if value is None:
        assert attr not in order_stats
    else:
        assert order_stats[attr] == value

@pytest.mark.parametrize("item, exc", [
    ("Eggs", False),
    ("Butter", False),
    ("Milk", True),
    ("Nonstick Spray", False),
])
def test_CheckInventory(cur_month, month_stats, item, exc):
    if exc:
        with pytest.raises(CheckInventory):
            create_order_stats(Items[item], cur_month, month_stats, override=False)
    else:
        create_order_stats(Items[item], cur_month, month_stats, override=False)

# test_items.py

from decimal import Decimal
import pytest

from csv_inv_order.database import *


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
    Inventory["Jan 01, 26", "Eggs", "consumed"].uncertainty = 5

    Butter  = [("estimate", 50), ("purchased", 24), ("consumed", 14), ("used", 10)]      # 50
    for code, num_units in Butter:
        Inventory.insert(date='Jan 01, 26', item="Butter", code=code, num_units=num_units)
    Inventory["Jan 01, 26", "Butter", "estimate"].uncertainty = 5
    Inventory["Jan 01, 26", "Butter", "consumed"].uncertainty = 10
    Inventory["Jan 01, 26", "Butter", "used"].uncertainty = 7

    Milk = [("count", 64), ("consumed", 32)]                                             # 32
    for code, num_units in Milk:
        Inventory.insert(date='Jan 01, 26', item="Milk", code=code, num_units=num_units)
    Inventory["Jan 01, 26", "Milk", "consumed"].uncertainty = 10

    Spray = [("count", 0.5), ("consumed", 0.4)]                                          # 0.1
    for code, num_units in Spray:
        Inventory.insert(date='Jan 01, 26', item="Nonstick Spray", code=code, num_units=num_units)
    Inventory["Jan 01, 26", "Nonstick Spray", "consumed"].uncertainty = 0.5

    Months.clear()
    Months.insert(month=1, year=2026, served_fudge=1.1, consumed_fudge=0.5, table_size=8,
                  staff_at_breakfast=10, tickets_claimed=173)                     # 200 w/fudge, 92 consumed
    Months.insert(month=2, year=2026, staff_at_breakfast=10, tickets_claimed=82)  # 100 w/fudge

@pytest.fixture
def cur_month():
    return Months[2026, 1]

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
    assert Items["Eggs"].calc_needed(200, 8) == 440
    assert Items["Butter"].calc_needed(200, 8) == 300
    assert Items["Milk"].calc_needed(200, 8) == 32
    assert Items["Nonstick Spray"].calc_needed(200, 8) == 1

def test_consumed():
    assert Items["Eggs"].consumed(92) == 202
    assert Items["Butter"].consumed(92) == 92
    assert Items["Milk"].consumed(92) == 32
    assert Items["Nonstick Spray"].consumed(92) == 1

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
    ("Butter", "min_needed1", 300),
    ("Butter", "min1", 2),
    ("Butter", "max1", 2),
    ("Butter", "consumed1", 92),
    ("Butter", "min_next", 156),
    ("Butter", "min_needed2", 248),
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
def test_order_stats(cur_month, item, attr, value):
    order_stats = Items[item].order_stats(cur_month, override=True)
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
def test_CheckInventory(cur_month, item, exc):
    if exc:
        with pytest.raises(CheckInventory):
            Items[item].order_stats(cur_month, override=False)
    else:
        Items[item].order_stats(cur_month, override=False)

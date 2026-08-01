# test_record_purchases.py

import pytest

from csv_inv_order.record_purchases import get_counts


class Order:
    def __init__(self, purchased_pkgs=None, purchased_units=None, qty=None):
        self.purchased_pkgs = purchased_pkgs
        self.purchased_units = purchased_units
        self.qty = qty

    def __repr__(self):
        return f"<Order: {self.purchased_pkgs=}, {self.purchased_units=}, {self.qty=}"

@pytest.mark.parametrize("order, result", [
    (Order(), {}),
    (Order(qty=0), {}),
    (Order(purchased_pkgs=0), {}),
    (Order(purchased_units=0), {}),
    (Order(purchased_pkgs=3, qty=2), {"num_pkgs": 3}),
    (Order(purchased_pkgs=2, qty=3), {"num_pkgs": 2}),
    (Order(purchased_pkgs=2), {"num_pkgs": 2}),
    (Order(qty=4), {"num_pkgs": 4}),
    (Order(purchased_units=20, qty=3), {"num_units": 20}),
    (Order(purchased_pkgs=2, purchased_units=20), {"num_pkgs": 2, "num_units": 20}),
])
def test_get_counts(order, result):
    assert get_counts(order) == result

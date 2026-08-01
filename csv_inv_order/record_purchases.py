# record_purchases.py

r'''
  - add "purchased" rows to Inventory table
  - update location and price in Products
  # write receipt slips (computer figures out bills?)
  #   -- don't have price paid, might go to two different people...
'''

import logging

from .database import *


logger = logging.getLogger('csv-inv-order.record_purchases')

def record_purchases(step, app):
    today = date.today()
    cur_month = Months.last_month()
    prev_yr, prev_mth = Months.dec_month(cur_month.year, cur_month.month)
    earliest = date(prev_yr, prev_mth, 15)
    latest = cur_month.breakfast_date
    if not app.testing:
        assert today >= earliest, \
               f"record_purchases: {today=:{Date_format}} < {earliest=:{Date_format}}"

    def date_is(purchase_date):        # a date (convert_fn parses the typed string)
        if not app.testing and not (earliest <= purchase_date <= latest):
            raise ValueError(f"{purchase_date=:{Date_format}} must be between "
                             f"{earliest:{Date_format}} and {latest:{Date_format}}")
        return record_purchases_in_inventory(step, app, purchase_date)

    app.screen.ask_question("Purchase date", date_is,
                            today.strftime(Date_format),
                            convert_fn=lambda s: datetime.strptime(s, Date_format).date())
    return None

def get_counts(order):
    r'''Returns count attrs to set on Inventory row.
    '''
    attrs = {}
    if order.purchased_units:
        attrs["num_units"] = order.purchased_units
        if order.purchased_pkgs is not None:
            attrs["num_pkgs"] = order.purchased_pkgs
    elif order.purchased_pkgs:
        attrs["num_pkgs"] = order.purchased_pkgs
    elif order.qty:
        attrs["num_pkgs"] = order.qty
    return attrs

def record_purchases_in_inventory(step, app, purchase_date):
    logger.info(f"record_purchases {purchase_date=:%b %d, %y}")

    num_orders = 0
    inv_rows_added = 0
    for order in Orders.values():
        if order.item not in Items:
            raise ValueError(f"{order.item=} not in Items table")
        num_orders += 1
        count_attrs = get_counts(order)
        if count_attrs:
            Inventory.insert(date=purchase_date, item=order.item, code="purchased", **count_attrs)
            inv_rows_added += 1
        if order.location is not None:
            logger.info(f"Updating Product[{order.product.item}, {order.product.supplier}, "
                        f"{order.product.supplier_id}].location to", order.location)
            order.product.location = order.location
        if order.price is not None:
            print(f"Updating Product[{order.product.item}, {order.product.supplier}, "
                                   f"{order.product.supplier_id}].price to", order.price)
            order.product.price = order.price

    logger.info(f"record_purchases: {num_orders=}, {inv_rows_added=}")
    logger.info("Clearing Orders")
    Orders.clear()
    app.set_changed()
    return step.mark_run(app)


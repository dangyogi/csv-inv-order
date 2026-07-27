# create_orders.py

import math

from .database import *


def create_orders(step, app, verbose=False):
    cur_month = Months.last_month()
    if not (4 <= cur_month.table_size <= 12):
        raise ValueError(f"{cur_month.table_size=} must be between 4 and 12")
    table_size = cur_month.table_size
    if not cur_month.served_fudge:
        raise ValueError(f"served_fudge not set in cur_month({cur_month.month_str}), aborting")

    avg_served1 = cur_month.avg_meals_served
    if cur_month.month == 4:
        avg_served2 = 0
        max_served2 = 0
    else:
        next_month = Months.inc_month(cur_month.year, cur_month.month)[1]
        avg_served2 = Months.avg_meals_served(next_month)
        max_served2 = Months.meals_planned(next_month, cur_month.served_fudge)
    max_served1 = cur_month.meals_planned
    num_tables = int(math.ceil(max_served1 / table_size))

    trace(f"cur_month={cur_month.month_str}, {avg_served1=}, served_fudge={cur_month.served_fudge}, "
          f"{max_served1=}, consumed_fudge={cur_month.consumed_fudge}, "
          f"{table_size=}, {num_tables=}")

    if cur_month.month in Month_stats:
        ms = Month_stats[cur_month.month]
        ms.max_served1 = max_served1
        ms.max_served2 = max_served2
        ms.served_fudge = cur_month.served_fudge
        ms.avg_served1 = avg_served1
        ms.avg_served2 = avg_served2
        ms.num_tables = num_tables
        ms.table_size = table_size
        ms.consumed_fudge = cur_month.consumed_fudge
    else:
        Month_stats.insert(month=cur_month.month, max_served1=max_served1, max_served2=max_served2,
                           served_fudge=cur_month.served_fudge, avg_served1=avg_served1, avg_served2=avg_served2,
                           num_tables=num_tables, table_size=table_size, consumed_fudge=cur_month.consumed_fudge)

    Orders.clear()
    Order_stats.clear()
    for item in Items.values():
        order_stats = item.order_stats(cur_month, override=True, verbose=verbose)

        optional_fields = {}
        for f in "max_order min_needed2 min_needed3".split():
            x = getattr(order_stats, f)
            if x is not None:
                optional_fields[f] = x
        Order_stats.insert(
          item=order_stats.item,
          unit=order_stats.unit,
          pkg_size=order_stats.pkg_size,
          perishable=order_stats.perishable,
          inv_units=order_stats.inv,
          uncertainty=order_stats.uncertainty,
          consumed1=order_stats.consumed1,
          consumed2=order_stats.consumed2,
          min_needed1=order_stats.min_needed1,
          order=order_stats.order,
          **optional_fields)

        if order_stats.order:
            Orders.insert(item=order_stats.item, qty=order_stats.order)

    app.set_changed()
    return step.mark_run(app)

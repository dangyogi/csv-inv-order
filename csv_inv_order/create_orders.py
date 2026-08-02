# create_orders.py

import math
import logging

from .database import *


logger = logging.getLogger('csv-inv-order.create_orders')

def create_month_stats(cur_month):
    r'''Returns Month_stats row.
    '''
    if not (4 <= cur_month.table_size <= 12):
        raise ValueError(f"{cur_month.table_size=} must be between 4 and 12")
    table_size = cur_month.table_size
    if not cur_month.served_fudge:
        raise ValueError(f"served_fudge not set in cur_month({cur_month.month_str}), aborting")

    avg_served1 = cur_month.avg_meals_served
    meals_planned1 = cur_month.meals_planned
    num_tables1 = cur_month.num_tables
    if cur_month.month == 4:
        next_month = None
        avg_served2 = None
        meals_planned2 = None
        num_tables2 = None
    else:
        next_month = Months.inc_month(cur_month.year, cur_month.month)[1]
        avg_served2 = Months.avg_meals_served(next_month)
        meals_planned2 = Months.meals_planned(next_month, cur_month.served_fudge)
        num_tables2 = Database.Months.num_tables(next_month, cur_month.served_fudge, table_size)

    logger.info(f"create_month_stats: cur_month={cur_month.month_str}, {next_month=}, "
                f"{avg_served1=}, {avg_served2=}, served_fudge={cur_month.served_fudge}, "
                f"{meals_planned1=}, {meals_planned2=}, "
                f"{num_tables1=}, {num_tables2=}, {table_size=}, "
                f"consumed_fudge={cur_month.consumed_fudge}")

    if cur_month.month in Month_stats:
        del Month_stats[cur_month.month]
    if next_month is None:
        opt = {}
    else:
        opt = dict(
            next_month=next_month,
            avg_served2=avg_served2,
            meals_planned2=meals_planned2,
            num_tables2=num_tables2,
        )
    Month_stats.insert(month=cur_month.month, avg_served1=avg_served1, served_fudge=cur_month.served_fudge,
                       meals_planned1=meals_planned1, num_tables1=num_tables1, table_size=table_size,
                       consumed_fudge=cur_month.consumed_fudge, **opt)
    return Month_stats[cur_month.month]

def create_order_stats(item, cur_month, override=False, verbose=False):
    r'''Returns dict to insert into order_stats.
    '''
    inv_units, uncertainty = item.in_stock(verbose=verbose)  # may be < 0
    if inv_units < 0:
        uncertainty += inv_units  # reduce uncertainty
        if uncertainty < 0:
            uncertainty = 0
        inv_units = 0
    stats = dict(item=item.item, unit=item.unit, pkg_size=item.pkg_size, perishable=item.perishable,
                 inv_units=inv_units, uncertainty=uncertainty)

    month_stats = Month_stats[cur_month.month]

    # in units
    min_needed1 = item.calc_needed(month_stats.meals_planned1, month_stats.num_tables1)
    stats.update(min_needed1=min_needed1)
    if inv_units - uncertainty >= min_needed1:
        # we have enough in stock already!  order 0
        stats.update(order=0)
        return stats

    # min pkgs needed assuming low-side (min) of inventory
    min1 = int(math.ceil((min_needed1 - max(0, inv_units - uncertainty)) / item.pkg_size))
    # max pkgs needed assuming high-side (max) of inventory, should be <= min1
    max1 = int(math.ceil((min_needed1 - (inv_units + uncertainty)) / item.pkg_size))
    stats.update(min1=min1, max1=max1)
    if verbose:
        print(f"{min_needed1=}; in_stock: {inv_units=}, {uncertainty=}; "
              f"min1 order: {min1}, max1 order: {max1}, pkg_size={item.pkg_size}")
    if item.perishable:
        if max1 < min1 and not override:
            # uncertainty crosses order line
            raise CheckInventory(item.item)
        stats.update(order=min1)
        return stats

    # else non_perishable
    # min consumed, in units, this month
    consumed1 = item.consumed(cur_month.consumed_fudge * month_stats.avg_served1,
                              month_stats.num_tables1, verbose)
    stats.update(consumed1=consumed1)
    if month_stats.next_month is not None:
        min_next = item.calc_needed(month_stats.meals_planned2, month_stats.num_tables2)
        stats.update(min_next=min_next)
    else:
        min_next = 0

    if verbose:
        print(f"{consumed1=}, {min_next=}")
    min_needed2 = consumed1 + min_next
    min2 = int(math.ceil((min_needed2 - max(0, inv_units - uncertainty)) / item.pkg_size))
    max2 = int(math.ceil((min_needed2 - (inv_units + uncertainty)) / item.pkg_size))
    stats.update(min_needed2=min_needed2, min2=min2, max2=max2)
    if verbose:
        print(f"{min_needed2=}, {min2=}, {max2=}")
    if min1 >= min2:
        if max1 < min1 and not override:
            # uncertainty crosses order line
            raise CheckInventory(item.item)
        stats.update(order=min1)
    else:  # min2 > min1
        if max2 < min2 and not override:
            # uncertainty crosses order line
            raise CheckInventory(item.item)
        stats.update(order=min2)
    return stats

def create_orders(step, app, verbose=False):
    cur_month = Months.last_month()
    create_month_stats(cur_month)   # just to be safe...

    Orders.clear()
    Order_stats.clear()
    for item in Items.values():
        order_stats = create_order_stats(item, cur_month, override=True, verbose=verbose)
        Order_stats.insert(**order_stats)
        order = order_stats['order']
        if order:
            Orders.insert(item=order_stats["item"], qty=order)

    app.set_changed()
    return step.mark_run(app)

# calc_estimates.py

r'''Inserts code="estimate" rows into Inventory table.
'''

from operator import attrgetter
import logging

from .actions import reset
from .database import *


logger = logging.getLogger('csv-inv-order.calc_estimates')

def calc_estimates(step, app, verbose=False):
    cur_month = Months.last_month()
    eff_date = max(cur_month.breakfast_date + timedelta(days=1), date.today())

    logger.info(f"Calculating estimates effective {eff_date:%b %d, %y}")

    for item in sorted(Items.values(), key=attrgetter("item")):
        units, uncertainty = item.in_stock(verbose)
        if verbose:
            logger.info(f"Item {item.item}: {units=}, {uncertainty=}")
        Inventory.insert(date=eff_date, item=item.item, code="estimate", num_units=units,
                         uncertainty=uncertainty)

    app.set_changed()
    return reset()

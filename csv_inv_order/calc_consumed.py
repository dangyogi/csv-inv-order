# calc_consumed.py

r'''Inserts code="consumed" rows into Inventory table.
'''

import math
import logging

from .database import *


logger = logging.getLogger('csv-inv-order.calc_consumed')

def calc_consumed(step, app):
    cur_month = Months.last_month()
    table_size = cur_month.table_size
    if not (4 <= table_size <= 12):
        raise ValueError(f"{table_size=} must be 4-12")
    def uncertainty_is(uncertainty_pct):
        if not (0.05 <= uncertainty_pct <= 0.50):
            raise ValueError(f"{uncertainty_pct=} must be 0.05-0.50")
        return calc_consumed2(step, app, cur_month, uncertainty_pct)
    app.screen.ask_question("Uncertainty (percent)", uncertainty_is, "0.20", convert_fn=float)
    return None


def calc_consumed2(step, app, cur_month, uncertainty_pct):
    eff_date = cur_month.breakfast_date
    meals_served = cur_month.meals_served
    if meals_served is None:
        raise ValueError(f"You haven't run set_bf_stats for {cur_month.month_str}")
    logger.info(f"Calculating consumption of {meals_served=}, {uncertainty_pct=}, "
                f"effective {eff_date:%b %d, %y}")

    for item in Items.values():
        units_consumed = item.consumed(meals_served, cur_month.num_tables)
        if units_consumed:
            uncertainty = int(math.ceil(units_consumed * uncertainty_pct))
            logger.info(f"Item {item.item}: {units_consumed} consumed, {uncertainty=}")
            Inventory.insert(date=eff_date, item=item.item, code="consumed", num_units=units_consumed,
                             uncertainty=uncertainty)
        else:
            logger.info(f"Item {item.item}: none consumed")

    app.set_changed()
    return step.mark_run(app)


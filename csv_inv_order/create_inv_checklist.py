# create_inv_checklist.py

from operator import attrgetter
import logging

from .database import *
from .create_orders import create_month_stats, create_order_stats


logger = logging.getLogger('csv-inv-order.create_inv_checklist')

def create_inv_checklist(step, app):
    app.screen.clear_message()
    cur_month = Months.last_month()
    if not (4 <= cur_month.table_size <= 12):
        raise ValueError(f"{cur_month.table_size=} must be between 4 and 12")
    logger.info(f"Create Inv_checklist: cur_month={cur_month.month_str}, {cur_month.table_size=}")
    create_month_stats(cur_month)
    if step.task.committed:
        if Inv_checklist:
            Inv_checklist.clear()
            app.set_changed()
            return step.mark_run(app)
    else:
        return load_inv_checklist(step, app, cur_month)

def load_inv_checklist(step, app, cur_month):
    Inv_checklist.clear()
    Order_stats.clear()
    for i in sorted(Items.values(), key=attrgetter('item')):
        order_stats = create_order_stats(i, cur_month)
        Order_stats.insert(**order_stats)
        if order_stats['chk_inventory']:
            Inv_checklist.insert(item=i.item)
    app.set_changed()
    return step.mark_run(app)


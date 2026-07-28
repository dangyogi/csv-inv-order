# create_inv_checklist.py

from operator import attrgetter
import logging

from .database import *


logger = logging.getLogger('csv-inv-order.create_inv_checklist')

def create_inv_checklist(step, app):
    app.screen.clear_message()
    if step.task.committed:
        if Inv_checklist:
            Inv_checklist.clear()
            app.set_changed()
            return step.mark_run(app)
    else:
        return load_inv_checklist(step, app)

def load_inv_checklist(step, app):
    cur_month = Months.last_month()
    if not (4 <= cur_month.table_size <= 12):
        raise ValueError(f"{cur_month.table_size=} must be between 4 and 12")
    logger.info(f"Create Inv_checklist: cur_month={cur_month.month_str}, {cur_month.table_size=}")

    Inv_checklist.clear()
    items = sorted(Items.values(), key=attrgetter('item'))
    if app.testing:
        Inv_checklist.insert(item=items[0].item)
        Inv_checklist.insert(item=items[1].item)
    else:
        for i in items:
            try:
                i.order(cur_month, verbose=False)
            except CheckInventory:
                Inv_checklist.insert(item=i.item)
    app.set_changed()
    return step.mark_run(app)


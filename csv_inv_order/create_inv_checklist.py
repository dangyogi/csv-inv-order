# create_inv_checklist.py

from operator import attrgetter
from functools import partial

from .database import *


def create_inv_checklist(step, app):
    app.screen.clear_message()
    if step.task.committed:
        if Inv_checklist:
            Inv_checklist.clear()
            app.set_changed()
            return step.mark_run(app)
    else:
        app.screen.ask_question("Table size", partial(load_inv_checklist, step, app), "8", convert_fn=int)

def load_inv_checklist(step, app):
    cur_month = Months.last_month()
    if not (4 <= cur_month.table_size <= 12):
        raise ValueError(f"{cur_month.table_size=} must be between 4 and 12")
    trace(f"Create Inv_checklist: cur_month={cur_month.month_str}, {cur_month.table_size=}")

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


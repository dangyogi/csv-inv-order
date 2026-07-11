# create_inv_checklist.py

from operator import attrgetter

from .database import *


def create_inv_checklist(step, app):
    def table_size_is(s):
        table_size = int(s)
        if table_size < 4 or table_size > 12:
            app.screen.show_error("Table size must be between 4 and 12")
            app.screen.clear_message()
            app.screen.ask_question("Table size", table_size_is, "8")
        else:
            return load_inv_checklist(table_size, step, app)
    app.screen.clear_message()
    if step.task.committed:
        if Inv_checklist:
            Inv_checklist.clear()
            app.set_changed()
            return step.mark_run(app)
    else:
        app.screen.ask_question("Table size", table_size_is, "8")

def load_inv_checklist(table_size, step, app):
    cur_month = Months.last_month()
    trace(f"Create Inv_checklist: cur_month={cur_month.month_str}, {table_size=}")

    Inv_checklist.clear()
    for i in sorted(Items.values(), key=attrgetter('item')):
        try:
            i.order(cur_month, table_size, verbose=False)
        except CheckInventory:
            Inv_checklist.insert(item=i.item)
    app.set_changed()
    return step.mark_run(app)


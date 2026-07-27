# calc_estimates.py

r'''Inserts code="estimate" rows into Inventory table.
'''

from .database import *


def calc_estimates(step, app, verbose=False):
    today = date.today()
    cur_month = Months.last_month()

    trace(f"Calculating estimates effective {today:%b %d, %y}")

    for item in Items.values():
        units, uncertainty = item.in_stock(verbose)
        if verbose:
            trace(f"Item {item.item}: {units=}, {uncertainty=}")
        Inventory.insert(date=today, item=item.item, code="estimate", num_units=units,
                         uncertainty=uncertainty)

    app.set_changed()
    return step.mark_run(app)

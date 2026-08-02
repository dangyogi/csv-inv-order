# read_inv.py

r'''Loads Inv_checklist into Transactions table.
'''

from operator import attrgetter
import logging

from .database import *


logger = logging.getLogger('csv-inv-order.read_inv')

def read_inv_command(step, app):
    logger.info(f"read_inv_command")
    # valid-date bounds don't depend on the answer -> compute once, before prompting
    today = date.today()
    cur_month = Months.last_month()
    earliest = date(cur_month.year, cur_month.month, 15)
    if not app.testing:
        assert today >= earliest, \
               f"read_inv_command: {today=:{Date_format}} < {earliest=:{Date_format}}"
    next_yr, next_mth = Months.inc_month(cur_month.year, cur_month.month)
    latest = min(date(next_yr, next_mth, 13), today)

    def date_is(inventory_date):        # a date (convert_fn parses the typed string)
        if not app.testing and not (earliest <= inventory_date <= latest):
            raise ValueError(f"{inventory_date:{Date_format}} must be between "
                             f"{earliest:{Date_format}} and {latest:{Date_format}}")
        return read_inv(inventory_date)

    def read_inv(inventory_date):
        logger.info(f"read_inv.read_inv({inventory_date=:{Date_format}})")
        changed = False
        for row in sorted(Inv_checklist.values(), key=attrgetter("item")):
            if row.num_pkgs or row.num_units:
                columns = dict(date=inventory_date, item=row.item, code="count")
                if row.num_pkgs:
                    columns['num_pkgs'] = row.num_pkgs
                if row.num_units:
                    columns['num_units'] = row.num_units
                Inventory.insert(**columns)
                changed = True
        if changed:
            app.set_changed()
        ans = step.mark_run(app)
        logger.info(f"read_inv -> {ans=}")
        return ans

    app.screen.ask_question("Inventory date", date_is,
                            today.strftime(Date_format),
                            convert_fn=lambda s: datetime.strptime(s, Date_format).date())
    logger.info(f"read_inv_command -> None")

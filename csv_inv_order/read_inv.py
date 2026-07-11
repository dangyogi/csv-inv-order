# read_inv.py

r'''Loads Inv_checklist into Transactions table.
'''

from .database import *


def date_is(date_str):
    trace(f"read_inv.date_is({date_str=})")
    effective_date = datetime.strptime(date_str, Date_format).date()
    today = date.today()
    cur_month = Months.last_month()
    earliest = date(cur_month.year, cur_month.month, 15)
    assert today >= earliest, f"read_inv.date_is: {today=:{Date_format}} < {earliest=:{Date_format}}"
    next_yr, next_mth = Months.inc_month(cur_month.year, cur_month.month)
    lastest = min(date(next_yr, next_mth, 13), today)
    if not (earliest <= effective_date <= latest):
        app.screen.show_error(
          f"{effective_date=:{Date_format}} must be between {earliest=:{Date_format}}  and {latest=:{Date_format}}")
        app.screen.clear_message()
        app.screen.ask_question("Effective date", date_is, date_str)
        trace(f"read_inv.date_is -> None")
    else:
        ans = read_inv(effective_date)
        trace(f"read_inv.date_is -> {ans}")
        return ans

def read_inv(effective_date):
    trace(f"read_inv.read_inv({effective_date=:{Date_format}})")
    changed = False
    for row in Inv_checklist.values():
        if row.num_pkgs or row.num_units:
            columns = dict(date=effective_date, item=row.item, code="count")
            if row.num_pkgs:
                columns['num_pkgs'] = row.num_pkgs
            if row.num_units:
                columns['num_units'] = row.num_units
            Inventory.insert(**columns)
            changed = True
    if changed:
        app.set_changed()
    ans = step.mark_run(app)
    trace(f"read_inv -> {ans=}")
    return ans

def read_inv_command(step, app):
    trace(f"read_inv_command")
    app.screen.ask_question("Effective date", date_is, date.today().strftime(Date_format))
    trace(f"read_inv_command -> None")

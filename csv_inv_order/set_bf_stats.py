# set_bf_stats.py

r'''Stores staff_at_breakfast and tickets_claimed in current Month.
'''

from .database import *


def set_bf_stats(step, app):
    cur_month = Months.last_month()
    def month_is(month):
        if app.testing:
            if not (1 <= month <= 12):
                raise ValueError(f"{month=} must be 1-12")
        else:
            if not (1 <= month <= 4 or 11 <= month <= 12):
                raise ValueError(f"{month=} must be 1-4 or 11-12")
        def year_is(year):
            try:
                target_month = Months[year, month]
            except KeyError:
                raise ValueError(f"{month=}/{year=} not in database")
            def staff_is(staff):
                if not (0 <= staff <= 50):
                    raise ValueError(f"{staff=} must be 0-50")
                def tickets_claimed_is(tickets_claimed):
                    if not (0 <= tickets_claimed <= 350):
                        raise ValueError(f"{tickets_claimed=} must be 0-350")
                    trace(f"Current month: {abbr_month(month)} '{str(year)[2:]}")
                    trace("Setting staff to", staff)
                    target_month.staff_at_breakfast = staff
                    trace("Tickets claimed to", tickets_claimed)
                    target_month.tickets_claimed = tickets_claimed
                    app.set_changed()
                    return step.mark_run(app)
                app.screen.ask_question("Tickets claimed", tickets_claimed_is, "", convert_fn=int)
                return None
            app.screen.ask_question("Staff at breakfast", staff_is, "", convert_fn=int)
            return None
        app.screen.ask_question("Year", year_is, str(cur_month.year), convert_fn=int)
        return None
    app.screen.ask_question("Month", month_is, str(cur_month.month), convert_fn=int)
    return None

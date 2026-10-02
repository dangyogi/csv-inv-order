# set_bf_stats.py

r'''Stores staff_at_breakfast and tickets_claimed in current Month.
'''

import logging

from .database import *


logger = logging.getLogger('csv-inv-order.set_bf_stats')

def set_bf_stats(step, app):
    cur_month = Months.last_month()
    def staff_is(staff):
        if not (0 <= staff <= 50):
            raise ValueError(f"{staff=} must be 0-50")
        def tickets_claimed_is(tickets_claimed):
            if not (0 <= tickets_claimed <= 350):
                raise ValueError(f"{tickets_claimed=} must be 0-350")
            logger.info(f"Current month: {abbr_month(cur_month.month)} '{str(cur_month.year)[2:]}")
            logger.info(f"Setting staff to {staff}")
            cur_month.staff_at_breakfast = staff
            logger.info(f"Setting tickets claimed to {tickets_claimed}")
            cur_month.tickets_claimed = tickets_claimed
            app.set_changed()
            return step.mark_run(app)
        app.screen.ask_question("Tickets claimed", tickets_claimed_is, "", convert_fn=int)
        return None
    app.screen.ask_question("Staff at breakfast", staff_is, "", convert_fn=int)
    return None

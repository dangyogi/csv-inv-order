# set_meeting_attendance.py

r'''Stores num_at_meeting in current Month.
'''

import logging

from .database import *


logger = logging.getLogger('csv-inv-order.set_meeting_attendance')

def set_meeting_attendance(step, app):
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
            def attendance_is(attendance):
                if not (0 <= attendance <= 150):
                    raise ValueError(f"{attendance=} must be 0-150")
                logger.info(f"Current month: {abbr_month(month)} '{str(year)[2:]}")
                logger.info(f"Setting num_at_meeting to {attendance}")
                target_month.num_at_meeting = attendance
                app.set_changed()
                return step.mark_run(app)
            app.screen.ask_question("Meeting attendance", attendance_is, "", convert_fn=int)
            return None
        app.screen.ask_question("Year", year_is, str(cur_month.year), convert_fn=int)
        return None
    app.screen.ask_question("Month", month_is, str(cur_month.month), convert_fn=int)
    return None


# set_meeting_attendance.py

r'''Stores num_at_meeting in current Month.
'''

import logging

from .database import *


logger = logging.getLogger('csv-inv-order.set_meeting_attendance')

def set_meeting_attendance(step, app):
    cur_month = Months.last_month()
    def attendance_is(attendance):
        if not (0 <= attendance <= 150):
            raise ValueError(f"{attendance=} must be 0-150")
        logger.info(f"Current month: {abbr_month(cur_month.month)} '{str(cur_month.year)[2:]}")
        logger.info(f"Setting num_at_meeting to {attendance}")
        cur_month.num_at_meeting = attendance
        app.set_changed()
        return step.mark_run(app)
    app.screen.ask_question("Meeting attendance", attendance_is, "", convert_fn=int)
    return None

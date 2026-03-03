# set_meeting_attendance.py

r'''Stores num_at_meeting in current Month.
'''

import sys

sys.path.append('.')
from database import *


def run():
    import argparse

    today = date.today()

    parser = argparse.ArgumentParser()
    parser.add_argument("--month", "-m", type=int, default=today.month)
    parser.add_argument("--year", "-y", type=int, default=today.year)
    parser.add_argument("--trial-run", "-t", action="store_true", default=False)
    parser.add_argument("attendance", type=int)

    args = parser.parse_args()

    month = args.month
    year = args.year

    print(f"Current month: {abbr_month(month)} '{str(year)[2:]}")

    load_database()

    cur_month = Months[year, month]

    print("Setting num_at_meeting to", args.attendance)
    cur_month.num_at_meeting = args.attendance

    if args.trial_run:
        print("Trial run: database not saved")
    else:
        print("Saving database")
        save_database()


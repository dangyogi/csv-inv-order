# new_month.py

r'''Stores num_at_meeting in current Month.
'''

import sys

sys.path.append('.')
from database import *


def run():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--trial-run", "-t", action="store_true", default=False)
    parser.add_argument("--new-month", "-m", type=int, default=None)

    args = parser.parse_args()
    trial_run = args.trial_run
    new_month = args.new_month

    load_database()

    last_month = list(Months.values())[-1]
    print(f"last_month: {last_month.month_str}, ", end='')

    if new_month is None:
        yr, mth = Months.inc_month(last_month.year, last_month.month)
        if mth == 5:
            print("You must explicitly specify May (month 5) with -m 5", file=sys.stderr)
            sys.exit(1)
    elif new_month < last_month.month:
        yr, mth = last_month.year + 1, new_month
    else:
        yr, mth = last_month.year, new_month
    Months.insert(year=yr, month=mth)
    new_month = Months[yr, mth]
    print(f"Created new_month {new_month.month_str}")

    if not args.trial_run:
        print("Saving Database")
        save_database()
    else:
        print("Trial_run: Database not saved")


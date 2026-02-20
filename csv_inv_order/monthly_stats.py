# monthly_stats.py

import sys

sys.path.append('.')
from database import *

from csv_app.report import *


def run():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", "-p", action="store_true", default=False)

    args = parser.parse_args()

    load_database()

    set_canvas("Monthly Stats")

    # month|years|#mtg|staff|tickets|served
    # Oct|24-26|a,b,c|...
    #    |avg|...
    report = Report(# 6 columns
                    title=(Centered(span=6, size="title", bold=True),),
                    header=(Left(bold=True), Left(bold=True), Right(bold=True), Right(bold=True),
                            Right(bold=True), Right(bold=True)),
                    body=(Left(), Left(), Right(), Right(), Right(), Right()),
                   )
    report.new_row("title", "Monthly Stats")
    report.new_row("header", "Month", "Years", "Num at Meeting", "Staff at BF", "Tickets Claimed", "    Served")

    for month in 10, 11, 12, 1, 2, 3, 4:
        stats = []  # (yr, ...)}
        for row in Months.values():
            if row.month == month:
                values = row.num_at_meeting, row.staff_at_breakfast, row.tickets_claimed, row.meals_served
                if any(values):
                    stats.append((row.year,) + values)
        def yr2(year):
            return str(year)[2:]
        if len(stats) == 1:
            yr_range = f"{yr2(stats[0][0])}"
        else:
            yr_range = f"{yr2(stats[0][0])}-{yr2(stats[-1][0])}"

        def gather(index):
            values = []
            for yr in stats:
                n = yr[index]
                if n is not None:
                    values.append(str(n))
            return ', '.join(values)

        report.new_row("body", abbr_month(month), yr_range, *map(gather, range(1, 5)))
        report.new_row("body", "", "avg",
                       Months.avg_num_at_meeting(month),
                       Months.avg_staff_at_breakfast(month),
                       Months.avg_tickets_claimed(month),
                       Months.avg_meals_served(month))

    if args.pdf:
        total_width, height = report.draw_init()
        report.draw()
        canvas_showPage()
        canvas_save()
    else:
        report.print_init()
        report.print()


if __name__ == "__main__":
    run()

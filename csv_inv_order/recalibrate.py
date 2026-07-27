# recalibrate.py

from operator import itemgetter
from itertools import groupby
from collections import defaultdict
import math

from .database import *


def get_counts():
    r'''For each range from count to count for the same item, this
    generates item, start_date, start_count, end_date, end_count - intervening adjustments, except consumed.
    '''
    delta = defaultdict(float)      # {item: delta}       added to second count
    starting_dates = {}             # {item: date}        date of starting count
    starting_counts = {}            # {item: total_units}
    for row in Inventory.values():
        if row.code == 'purchased':
            delta[row.item] -= row.total_units
        elif row.code == 'used':
            delta[row.item] += row.total_units
        elif row.code == 'count':
            if row.item in starting_dates:
                yield (row.item, starting_dates[row.item], starting_counts[row.item],
                                 row.date, row.total_units + delta[row.item])
            if row.item in delta:
                del delta[row.item]
            starting_dates[row.item] = row.date
            starting_counts[row.item] = row.total_units

def get_breakfast(date):
    r'''Returns the month with the greatest breakfast_date <= date.
    '''
    ans = None
    for month in Months.values():
        if month.breakfast_date <= date and (ans is None or month.breakfast_date > ans.breakfast_date):
            ans = month
    return ans

def run():
    load_database()
    table_size = Months.last_month().table_size
    for item, counts in groupby(sorted(get_counts()), key=itemgetter(0)):
        item_obj = Items[item]
        if item_obj.num_per_serving is not None:
            print(f"{item}: stored num_per_serving={item_obj.num_per_serving}", end='')
            def final(consumed, total_served, total_tables, total_months):
                return f"per_serving={consumed/total_served:.02f}"
        elif item_obj.num_per_meal is not None:
            print(f"{item}: stored num_per_meal={item_obj.num_per_meal}", end='')
            def final(consumed, total_served, total_tables, total_months):
                return f"per_meal={consumed/total_months:.02f}"
        elif item_obj.num_per_table is not None:
            print(f"{item}: stored num_per_table={item_obj.num_per_table}", end='')
            def final(consumed, total_served, total_tables, total_months):
                return f"per_table={consumed/total_tables:.02f}"
        else:
            print(f"{item}: no stored consumption set")
            def final(consumed, total_served, total_tables, total_months):
                return None
        grand_total_served = 0
        grand_total_tables = 0
        grand_total_months = 0
        grand_total_consumed = 0
        lines = []  # list of lines, which are list of comma separated texts
        for item, start_date, start_count, end_date, end_count in counts:
            last_breakfast = get_breakfast(end_date)
            total_served = 0
            total_tables = 0
            total_months = 0
            month = get_breakfast(start_date)  # don't count this one!
            while True:
                month = Months[Months.inc_month(month.year, month.month)]
                if month.key() > last_breakfast.key():
                    break
                total_served += month.meals_served
                total_tables += int(math.ceil(total_served / table_size))
                total_months += 1
            consumed = start_count - end_count
            grand_total_served += total_served
            grand_total_tables += total_tables
            grand_total_months += total_months
            grand_total_consumed += consumed
            line = [f"  {item=}, start={start_date:'%b %d, %y'}, end={end_date:'%b %d, %y'}, "
                    f"served={total_served}, months={total_months}, {consumed=:.02f}"]
            if total_served:
                text2 = final(consumed, total_served, total_tables, total_months)
                if text2:
                    line.append(text2)
            lines.append(line)
        text2 = final(grand_total_consumed, grand_total_served, grand_total_tables, grand_total_months)
        if text2:
            print(',', text2)
        else:
            print()
        for line in lines:
            print(', '.join(line))


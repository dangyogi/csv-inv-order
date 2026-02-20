# recalibrate.py

from operator import itemgetter
from itertools import groupby
from collections import defaultdict

from .database import *


def get_counts():
    delta = defaultdict(float)  # {item: delta}       added to second count
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
        if month.breakfast_date <= date:
            ans = month
    return ans

def run():
    load_database()
    for item, counts in groupby(sorted(get_counts()), key=itemgetter(0)):
        item_counts = list(counts)
        item_obj = Items[item]
        if item_obj.num_per_serving is not None:
            print(f"{item}: stored num_per_serving={item_obj.num_per_serving}")
        elif item_obj.num_per_meal is not None:
            print(f"{item}: stored num_per_meal={item_obj.num_per_meal}")
        elif item_obj.num_per_table is not None:
            print(f"{item}: stored num_per_table={item_obj.num_per_table}")
        else:
            print(f"{item}: no stored consumption set")
        for item, start_date, start_count, end_date, end_count in item_counts:
            last_breakfast = get_breakfast(end_date)
            total_served = 0
            month = get_breakfast(start_date)  # don't count this one!
            while True:
                month = Months[Months.inc_month(month.year, month.month)]
                if month.key() > last_breakfast.key():
                    break
                total_served += month.meals_served
            consumed = start_count - end_count
            print(f"  {item=}, {total_served=}, {consumed=:.02f}", end='')
            if total_served:
                print(f", num_per_serving={consumed/total_served:.02f}")
            else:
                print()


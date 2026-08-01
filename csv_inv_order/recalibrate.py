# recalibrate.py

from operator import itemgetter
from itertools import groupby
from collections import defaultdict
import math

from .database import *


def get_counts():
    r'''For each range from count to count for the same item, this generates
    item, start_date, start_count, end_date, end_count - intervening adjustments, except consumed.
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

def get_line1(item):
    r'''Returns head (to be printed immediately, not printed here to make testing easier), tail_fn.

    tail_fn takes (consumed, total_served, total_tables, total_months) and returns the tail of the message
    to be printed at the end of head above after the caller has figured out the parameters to this
    function.
    '''
    item_obj = Items[item]
    if item_obj.num_per_serving is not None:
        head = f"{item}: stored num_per_serving={item_obj.num_per_serving}"
        def tail_fn(consumed, total_served, total_tables, total_months):
            return f"per_serving={consumed/total_served:.02f}"
    elif item_obj.num_per_meal is not None:
        head = f"{item}: stored num_per_meal={item_obj.num_per_meal}"
        def tail_fn(consumed, total_served, total_tables, total_months):
            return f"per_meal={consumed/total_months:.02f}"
    elif item_obj.num_per_table is not None:
        head = f"{item}: stored num_per_table={item_obj.num_per_table}"
        def tail_fn(consumed, total_served, total_tables, total_months):
            return f"per_table={consumed/total_tables:.02f}"
    else:
        head = f"{item}: no stored consumption set"
        def tail_fn(consumed, total_served, total_tables, total_months):
            return None
    return head, tail_fn

def process_counts(tail_fn, counts, table_size):
    r'''Returns tail for line1, and lines to print after line1.

    Each element in lines is a list of phrases to be joined by commas.
    '''
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
        yr_month = get_breakfast(start_date).key()  # don't count this one!
        while True:
            yr_month = Months.inc_month(*yr_month)
            if yr_month > last_breakfast.key():
                break
            if yr_month in Months:
                month = Months[yr_month]
                total_served += month.meals_served
                total_tables += int(math.ceil(month.meals_served / table_size))
                total_months += 1
        consumed = start_count - end_count
        grand_total_served += total_served
        grand_total_tables += total_tables
        grand_total_months += total_months
        grand_total_consumed += consumed
        phrases = [f"  {item=}, start={start_date:{Date_format}}, end={end_date:{Date_format}}, "
                   f"served={total_served}, months={total_months}, {consumed=:.02f}"]
        if total_served:
            tail = tail_fn(consumed, total_served, total_tables, total_months)
            if tail:
                phrases.append(tail)
        lines.append(phrases)
    tail = tail_fn(grand_total_consumed, grand_total_served, grand_total_tables, grand_total_months)
    return tail, lines

def run():
    load_database()
    table_size = Months.last_month().table_size
    for item, counts in groupby(sorted(get_counts()), key=itemgetter(0)):
        head, tail_fn = get_line1(item)
        print(head, end='')
        tail, lines = process_counts(tail_fn, counts, table_size)
        if tail:
            print(',', tail)
        else:
            print()
        for phrases in lines:
            print(', '.join(phrases))


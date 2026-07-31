# est_cost_per_meal.py

r'''
Reports the avg cost per meal served.

Adds up cost_per_meal (units_consumed * price_per_unit) / avg_tickets_claimed for each item in Items.

Displays the sum.  This includes the cost of feeding staff served divided by tickets_claimed.

Does not include 50/50.
'''


from statistics import mean
import curses
import logging

from .database import *


logger = logging.getLogger('csv-inv-order.est_cost_per_meal')

def est_cost_per_meal(step, app):
    avg_meals_served = mean(Months.avg_meals_served(mth) for mth in (1,2,3,4,11,12))
    avg_tickets_claimed = mean(Months.avg_tickets_claimed(mth) for mth in (1,2,3,4,11,12))
    table_size = Months.last_month().table_size
    avg_num_tables = avg_tickets_claimed / table_size

    logger.info(f"est_cost_per_meal: {avg_meals_served=}, {avg_tickets_claimed=}, "\
                f"{avg_num_tables=:.2f}, {table_size=}")

    if not (4 <= table_size <= 12):
        raise ValueError(f"{table_size=} must be 4-12")

    cost_per_meal = 0
    for item in Items.values():
        cost_per_meal += item.consumed(avg_meals_served, avg_num_tables) * float(item.product.price_per_unit)

    cost_per_meals_served = cost_per_meal / avg_meals_served
    cost_per_tickets_claimed = cost_per_meal / avg_tickets_claimed
    screen = app.screen
    screen.show_message(f"Est cost per meal served {cost_per_meals_served:.2f}, "
                        f"per tickets claimed {cost_per_tickets_claimed:.2f}",
                        curses.color_pair(screen.default_pair))
    return None


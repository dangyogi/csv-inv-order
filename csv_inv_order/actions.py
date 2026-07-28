# actions.py

from csv_app.action import *
from csv_app.report import dump_table
from tui_app.table_screen import table_screen
from tui_app.row_screen import row_screen
from . import tables
from .database import *
from .create_inv_checklist import create_inv_checklist
from .read_inv import read_inv_command
from .create_orders import create_orders
from .create_POs import create_POs
from .set_meeting_attendance import set_meeting_attendance
from .set_bf_stats import set_bf_stats
from .record_purchases import record_purchases
from .calc_consumed import calc_consumed
from .calc_estimates import calc_estimates
from .est_cost_per_meal import est_cost_per_meal


def table(table_name, validate_fn=None, mark_run=True):
    def run_table_screen(step, app):
        if mark_run:
            step.mark_run(app)
        return table_screen(tables.Tables[table_name], back=app.screen, validate_fn=validate_fn)
    return run_table_screen

def validate_inv_checklist(table):
    for row in table.values():
        if row.num_pkgs is None and row.num_units is None:
            return f"No count entered for {row.item}"

def validate_orders(table):
    for row in table.values():
        if row.qty is None:
            return f"No order quantity entered for {row.item}"

def stub(step, app):
    trace(f"stub {step.name}")
    app.set_changed()
    return step.mark_run(app)

def save(step, app):
    trace(f"save {step.name}")
    if not app.testing:
        save_database()
    app.reset_changed()
    return step.mark_run(app)

def print(table_name):
    def print_table(step, app):
        dump_table(table_name, pdf=True, load=False)
        return step.mark_run(app)
    return print_table

class ExitStep(Step):
    def __init__(self, id, task, abort=False):
        super().__init__(id, task, self.fn)
        self.abort = abort

    @property
    def can_run(self):
        return self.app.changed == self.abort

    def fn(self, step, app):
        if self.abort:
            return "APP_ABORT"
        return "APP_EXIT"


def last_month_update(global_validate=None):
    return lambda step, app: \
             row_screen.for_update(Months.last_month(), app.screen,
                                   global_validate=global_validate,
                                   callback=lambda: step.mark_run(app))

def create_month(step, app):
    def year_is(year):                       # already an int (convert_fn=int)
        def month_is(month):                 # already an int
            if app.testing:
                if not (1 <= month <= 12):
                    raise ValueError(f"{month=} must be 1-12")
            else:
                if not (1 <= month <= 4 or 11 <= month <= 12):
                    raise ValueError(f"{month=} must be 1-4 or 11-12")
            trace(f"month_is: {month=}")
            Months.insert(year=year, month=month, served_fudge=1.35, consumed_fudge=0.9)
            app.set_changed()
            return step.mark_run(app)
        trace(f"year_is: {year=}")
        today = date.today()
        if not (today.year <= year <= today.year + 1):
            raise ValueError(f"Invalid {year=}, must be between {today.year} and {today.year + 1}")
        app.screen.ask_question("month", month_is, str(next_mth), convert_fn=int)
    last_month = Months.last_month()
    yr, mth = last_month.year, last_month.month
    if mth == 4:
        next_yr, next_mth = yr, 11
    else:
        next_yr, next_mth = Months.inc_month(yr, mth)
    trace(f"create_month: {yr=}, {mth=}, {next_yr=}, {next_mth=}")
    app.screen.ask_question("year", year_is, str(next_yr), convert_fn=int)

def check_fudge_factors(row_screen):
    other = None
    for field in row_screen.fields:
        trace(f"check_fudge_factors: got {field.name=}")
        if field.name == 'served_fudge':
            if field.text:
                fudge = float(field.text)
                if 0.9 <= fudge <= 1.45:
                    # OK
                    if other == 'consumed_fudge':
                        return None  # no errors!
                    else:
                        other = 'served_fudge'
                else:
                    return f"served_fudge must be between 0.9 and 1.45, got {fudge}"
            else:
                return "You must set served_fudge between 0.9 and 1.45, watching meals_planned"
        elif field.name == 'consumed_fudge':
            if field.text:
                fudge = float(field.text)
                if 0.6 <= fudge <= 1.0:
                    # OK
                    if other == 'served_fudge':
                        return None  # no errors!
                    else:
                        other = 'consumed_fudge'
                else:
                    return f"consumed_fudge must be between 0.6 and 1.0, got {fudge}"
            else:
                return "You must set consumed_fudge between 0.6 and 1.0, to count on next month's consumption"
    raise AssertionError(f"check_fudge_factors: didn't find fudge attrs in row_screen.fields")


# step kw args: can_rerun=False, can_rerun_after_commit=False, commits_task=False, disable_prereqs=False

# create new month
Step(1, None, create_month)


# do inventory
Task2 = Task(2, 1, can_rerun_after_commit=True)

# set fudge factors and table_size
Step(21, Task2, last_month_update(check_fudge_factors), 1, can_rerun=True)

# create Inv_checklist
Step(22, Task2, create_inv_checklist, 21, can_rerun=True, can_rerun_after_commit=True)

# print Inv_checklist
Step(23, Task2, print("Inv_checklist"), 22, can_rerun=True)

# edit Inv_checklist
Step(24, Task2, table('Inv_checklist', validate_inv_checklist), 23, can_rerun=True)

# import Inv_checklist
Step(25, Task2, read_inv_command, 24, commits_task=True)


# create POs
Task3 = Task(3, 2)

# create Orders
Step(31, Task3, create_orders, 25, can_rerun=True, can_rerun_after_commit=True)

# edit Orders
Step(32, Task3, table('Orders', validate_orders), 31, can_rerun=True, can_rerun_after_commit=True)

# create P.O.s
Step(33, Task3, create_POs, 32, can_rerun=True, can_rerun_after_commit=True)


# after member meeting
Task4 = Task(4, 3)

# set meeting attendance
Step(41, Task4, set_meeting_attendance, 1, can_rerun=True, can_rerun_after_commit=True)

# edit purchases/locations/prices
Step(42, Task4, table('Orders'), 33, can_rerun=True)

# import purchases/locations/prices
Step(43, Task4, record_purchases, 42, commits_task=True)


# after breakfast
Task5 = Task(5, 1)

# set breakfast stats
Step(51, Task5, set_bf_stats, 1, can_rerun=True)

# calc consumed
Step(52, Task5, calc_consumed, 51, disable_prereqs=True)

# calc estimates
Step(53, Task5, calc_estimates, 25, 43, 52, commits_task=True)


# view/edit tables
Task6 = Task(6, column_break=True)

# Items
Step(61, Task6, table("Items", mark_run=False), can_rerun=True)

# Products
Step(62, Task6, table("Products", mark_run=False), can_rerun=True)

# Inventory
Step(63, Task6, table("Inventory", mark_run=False), can_rerun=True)

# Months
Step(64, Task6, table("Months", mark_run=False), can_rerun=True)

# Inv_checklist
Step(65, Task6, table("Inv_checklist", mark_run=False), can_rerun=True)

# Orders
Step(66, Task6, table("Orders", mark_run=False), can_rerun=True)

# Order_stats
Step(67, Task6, table("Order_stats", mark_run=False), can_rerun=True)

# Month_stats
Step(68, Task6, table("Month_stats", mark_run=False), can_rerun=True)

# Steps
Step(69, Task6, table("Steps", mark_run=False), can_rerun=True)


# other
Task7 = Task(7)

# save database
Step(71, Task7, save, can_rerun=True)

# est_cost_per_meal
Step(72, Task7, est_cost_per_meal, can_rerun=True)

# git commit/push
Step(73, Task7, stub, can_rerun=True)

# exit
ExitStep(74, Task7)

# abort
ExitStep(75, Task7, abort=True)


# special events
Task8 = Task(8)

# acquisitions
Step(81, Task8, stub, can_rerun=True)

# used
Step(82, Task8, stub, can_rerun=True)


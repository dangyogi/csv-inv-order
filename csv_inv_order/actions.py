# actions.py

import logging

from csv_app.action import *
from csv_app.report import dump_table
from tui_app.tui import get_app
from tui_app.table_screen import table_screen
from tui_app.row_screen import row_screen
from tui_app.run_program import git_commit_push, print_file
from tui_app.print_sheet import print_sheet
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


logger = logging.getLogger('csv-inv-order.actions')

def table(table_name, validate_fn=None, mark_run=True):
    def run_table_screen(step, app):
        if mark_run:
            step.mark_run(app)
        return table_screen(tables.Tables[table_name], back=app.screen, validate_fn=validate_fn)
    return run_table_screen

def validate_inv_checklist(table):
    logger.info(f"validate_inv_checklist")
    for row in table.values():
        logger.info(f"  row {row.item=}, {row.num_pkgs=}, {row.num_units=}")
        if row.num_pkgs is None and row.num_units is None:
            logger.info(f"  failed")
            return f"No count entered for {row.item}"

def validate_orders(table):
    for row in table.values():
        if row.qty is None:
            return f"No order quantity entered for {row.item}"

def stub(step, app):
    logger.info(f"stub {step.name}")
    app.set_changed()
    return step.mark_run(app)

def save(step, app):
    logger.info(f"save {step.name}")
    step.mark_run(app)    # sets app.changed, run this first so mark is saved
    if not app.testing:
        save_database()
    app.reset_changed()
    return 'REFRESH'

def print(table_name):
    def print_table(step, app):
        dump_table(table_name, pdf=True, load=False)
        return lp_file(f"{table_name}.pdf")(step, app)
    return print_table

def lp_file(filename, copies=1, portrait=True):
    def lp(step, app):
        print_file("~/Documents/" + filename, copies=copies, portrait=portrait)
        return step.mark_run(app)
    return lp

def lp_POs(copies=1):
    def lp(step, app):
        print_file("~/Documents/" + f"Purchase-Orders-{Months.last_month().po_num}.pdf", copies=copies)
        return step.mark_run(app)
    return lp

def print_form(sheet, copies=1, mark_run=True):
    def print_form_step_fn(step, app):
        print_sheet(sheet, copies)
        if mark_run:
            return step.mark_run(app)
        return None
    return print_form_step_fn

def git_commit(step, app):
    def message_is(message):
        git_commit_push(message, [get_database_filename()],
                        partial(app.screen.show_message, attr=app.screen.default_pair))
        return step.mark_run(app)
    app.screen.ask_question("Commit message", message_is, "")
    return None

class ExitStep(Step):
    def __init__(self, id, task, abort=False, ok_fn=None):
        super().__init__(id, task, self.fn, ok_fn=ok_fn)
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
            logger.info(f"month_is: {month=}")
            Months.insert(year=year, month=month, served_fudge=1.35, consumed_fudge=0.9)
            app.set_changed()
            return step.mark_run(app)
        logger.info(f"year_is: {year=}")
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
    logger.info(f"create_month: {yr=}, {mth=}, {next_yr=}, {next_mth=}")
    app.screen.ask_question("year", year_is, str(next_yr), convert_fn=int)

def check_fudge_factors(row_screen):
    other = None
    for field in row_screen.fields:
        logger.info(f"check_fudge_factors: got {field.name=}")
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
Step(24, Task2, table('Inv_checklist', validate_inv_checklist), 22, can_rerun=True)

# import Inv_checklist
Step(25, Task2, read_inv_command, 24, commits_task=True)


# create POs
Task3 = Task(3, 2)

# create Orders
Step(31, Task3, create_orders, 25, can_rerun=True, can_rerun_after_commit=True)

# edit Orders
Step(32, Task3, table('Orders', validate_orders), 31, can_rerun=True, can_rerun_after_commit=True)

# create P.O.s
Step(33, Task3, create_POs, 32)

# print P.O.s
Step(34, Task3, lp_POs(copies=3), 33,
     can_rerun=True, can_rerun_after_commit=True, commits_task=True)


# print forms
Task4 = Task(4, 3)

# member sign in
Step(41, Task4, print_form('member_sign_in', copies=2), can_rerun=True, can_rerun_after_commit=True)

# advance ticket sales
Step(42, Task4, print_form('adv_ticket_sales'), can_rerun=True, can_rerun_after_commit=True)

# inv check list
Step(43, Task4, print_form('inv_check_list'), can_rerun=True, can_rerun_after_commit=True)


# after member meeting
Task5 = Task(5, 3)

# set meeting attendance
Step(51, Task5, set_meeting_attendance, 1, can_rerun=True, can_rerun_after_commit=True)

# edit purchases/locations/prices
Step(52, Task5, table('Orders'), 33, can_rerun=True)

# import purchases/locations/prices
Step(53, Task5, record_purchases, 52, commits_task=True)


# after breakfast
Task6 = Task(6, 1)

# set breakfast stats
Step(61, Task6, set_bf_stats, 1, can_rerun=True)

# calc consumed
Step(62, Task6, calc_consumed, 61, disable_prereqs=True)

# calc estimates
Step(63, Task6, calc_estimates, 25, 53, 62, commits_task=True)


# view/edit tables
Task7 = Task(7, column_break=True)

# Items
Step(71, Task7, table("Items", mark_run=False), can_rerun=True)

# Products
Step(72, Task7, table("Products", mark_run=False), can_rerun=True)

# Inventory
Step(73, Task7, table("Inventory", mark_run=False), can_rerun=True)

# Months
Step(74, Task7, table("Months", mark_run=False), can_rerun=True)

# Inv_checklist
Step(75, Task7, table("Inv_checklist", mark_run=False), can_rerun=True)

# Orders
Step(76, Task7, table("Orders", mark_run=False), can_rerun=True)

# Order_stats
Step(77, Task7, table("Order_stats", mark_run=False), can_rerun=True)

# Month_stats
Step(78, Task7, table("Month_stats", mark_run=False), can_rerun=True)

# Steps
Step(79, Task7, table("Steps", mark_run=False), can_rerun=True)


# other
Task8 = Task(8)

# save database
Step(81, Task8, save, ok_fn=lambda: get_app().changed, can_rerun=True)

# est_cost_per_meal
Step(82, Task8, est_cost_per_meal, can_rerun=True)

# git commit/push
Step(83, Task8, git_commit, 81, ok_fn=lambda: not get_app().changed, can_rerun=True)

# exit
ExitStep(84, Task8, ok_fn=lambda: not get_app().changed)

# abort
ExitStep(85, Task8, abort=True, ok_fn=lambda: get_app().changed)

# run recalibrate (at shell prompt)
Step(86, Task8, stub, can_rerun=True)


# special events
Task9 = Task(9)

# acquisitions
Step(91, Task9, stub, can_rerun=True)

# used
Step(92, Task9, stub, can_rerun=True)


# actions.py

from csv_app.action import *


def stub(step, app):
    app.trace(step.name)
    return None  # no error

# step kw args: can_rerun=False, can_rerun_after_commit=False, commits_task=False, disable_prereqs=False

# create new month
Step(1, None, stub)


# do inventory
Task2 = Task(2, 1, can_rerun_after_commit=True)

# set fudge factors
Step(21, Task2, stub, 1, can_rerun=True, can_rerun_after_commit=True)

# create Inv_checklist
Step(22, Task2, stub, 21, can_rerun=True)

# print Inv_checklist
Step(23, Task2, stub, 22, can_rerun=True)

# edit Inv_checklist
Step(24, Task2, stub, 22, can_rerun=True)

# import Inv_checklist
Step(25, Task2, stub, 24, commits_task=True)


# create POs
Task3 = Task(3, 2)

# create Orders
Step(31, Task3, stub, 25, can_rerun=True)

# edit Orders
Step(32, Task3, stub, 31, can_rerun=True)

# create P.O.s
Step(33, Task3, stub, 32, can_rerun=True)

# print P.O.s
Step(34, Task3, stub, 33, can_rerun=True)


# after member meeting
Task4 = Task(4, 3)

# set meeting attendance
Step(41, Task4, stub, can_rerun=True, can_rerun_after_commit=True)

# edit purchases/locations/prices
Step(42, Task4, stub, 33, can_rerun=True)

# import purchases/locations/prices
Step(43, Task4, stub, 42, commits_task=True)


# after breakfast
Task5 = Task(5, 1)

# set breakfast stats
Step(51, Task5, stub, can_rerun=True)

# calc consumed
Step(52, Task5, stub, 51, disable_prereqs=True)

# calc estimates
Step(53, Task5, stub, 25, 43, 52, commits_task=True)


# other
Task6 = Task(6, column_break=True)

# view/edit tables
Step(61, Task6, stub, can_rerun=True)

# monthly stats
Step(62, Task6, stub, can_rerun=True)

# recalibrate
Step(63, Task6, stub, can_rerun=True)

# git commit/push
Step(64, Task6, stub)


# special events
Task7 = Task(7)

# acquisitions
Step(71, Task7, stub, can_rerun=True)

# used
Step(72, Task7, stub, can_rerun=True)


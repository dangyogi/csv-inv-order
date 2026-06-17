# actions.py

from csv_app.action import *


def stub(step, app):
    app.trace(step.name)


# create new month
Step(1, None, stub)


# do inventory
Task2 = Task(2, 1)

# set fudge factors
Step(21, Task2, stub, 1)

# create Inv_checklist
Step(22, Task2, stub, 21)

# print Inv_checklist
Step(23, Task2, stub, 22)

# edit Inv_checklist
Step(24, Task2, stub, 22)

# import Inv_checklist
Step(25, Task2, stub, 24)


# create POs
Task3 = Task(3, 2)

# create Orders
Step(31, Task3, stub, 25)

# edit Orders
Step(32, Task3, stub, 31)

# create P.O.s
Step(33, Task3, stub, 32)

# print P.O.s
Step(34, Task3, stub, 33)


# after member meeting
Task4 = Task(4, 3)

# set meeting attendance
Step(41, Task4, stub)

# edit purchases/locations/prices
Step(42, Task4, stub, 33)

# import purchases/locations/prices
Step(43, Task4, stub, 42)


# after breakfast
Task5 = Task(5, 1)

# set breakfast stats
Step(51, Task5, stub)

# calc consumed
Step(52, Task5, stub, 51)

# calc estimates
Step(53, Task5, stub, 52)


# other
Task6 = Task(6)

# view/edit tables
Step(61, Task6, stub)

# monthly stats
Step(62, Task6, stub)

# recalibrate
Step(63, Task6, stub)

# git commit/push
Step(64, Task6, stub)


# special events
Task7 = Task(7)

# acquisitions
Step(71, Task7, stub)

# used
Step(72, Task7, stub)


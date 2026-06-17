# tui.py

from tui_app import tui
from . import database
from . import actions    # somebody has to import this to get the module initialized


def run():
    database.load_database()
    tui.start(database.Tables)


if __name__ == "__main__":
    run()

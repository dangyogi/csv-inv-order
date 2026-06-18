# tui.py

from tui_app import tui
from tui_app.menu_screen import menu_screen
from csv_app import action
from . import database
from . import actions    # somebody has to import this to get the module initialized


def run():
    database.load_database()
    tui.start(database.Tables, menu_screen(action.Actions, title="Action Menu"))


if __name__ == "__main__":
    run()

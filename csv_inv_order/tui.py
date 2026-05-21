# tui.py

from . import database
from tui_app import tui

def run():
    database.load_database()
    tui.start(database.Tables)


if __name__ == "__main__":
    run()

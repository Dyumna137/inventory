"""
main.py - application entry point
Run from project root:
    python main.py
"""

from core.config import DB_PATH
from db import database
from gui import gui

if __name__ == "__main__":
    # Initialize DB (ensures file + default inventory table exists)
    database.init_db(db_path=DB_PATH, table_name="inventory")
    # Launch the GUI
    gui.run_gui()

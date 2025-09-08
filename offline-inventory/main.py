# main.py (Entry point, optional)
import db.database as database
import gui.gui as gui

if __name__ == "__main__":
    database.init_db()
    gui.run_gui()

import os

POSSIBLE_DB_PATHS = ["offline-inventory/db/inventory.db", "db/inventory.db"]


def find_db_path():
    for path in POSSIBLE_DB_PATHS:
        if os.path.exists(path):
            return path
    raise FileNotFoundError("Database file not found in any known location.")


DB_NAME = find_db_path()

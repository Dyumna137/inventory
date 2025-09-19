"""
database.py
===========

Database persistence layer for the inventory project.

This module provides:
- Core inventory database schema initialization
- CRUD operations (insert, fetch, delete, update)
- Helper for saving Pandas DataFrames to any table (for datasheet import)
- Support for multiple databases and dynamic table selection

Dependencies:
-------------
- sqlite3 (standard library)
- SQLAlchemy (for flexible Pandas-to-SQL handling)
- Pandas (for dataframe operations)

Typical usage:
--------------
>>> from db.database import init_db, insert_item, fetch_items, get_table_names
>>> init_db()
>>> insert_item("Keyboard", 5, 1200.50, "inventory", "data/inventory.db")
>>> print(fetch_items("inventory", "data/inventory.db"))
[("Keyboard", 5, 1200.5)]
"""

import sqlite3
from typing import List, Tuple
from core.config import DB_PATH  # <- unified config constant name
from sqlalchemy import create_engine
import pandas as pd
from pathlib import Path

# ------------------------------
# Generic Utilities
# ------------------------------


def connect_db(db_path: str = DB_PATH) -> sqlite3.Connection:
    """
    Establish a connection to the SQLite database.

    Args:
        db_path (str): Path to the database file (defaults to core.config.DB_PATH)

    Returns:
        sqlite3.Connection: Database connection object
    """
    # Ensure parent folder exists so sqlite can create the file
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(db_path)


def init_db(db_path: str = DB_PATH, table_name: str = "inventory") -> None:
    """
    Initialize the database with the required table if not already present.

    Args:
        db_path (str): Path to the database file
        table_name (str): Table to initialize (default 'inventory')

    Creates:
        - inventory (id, name, quantity, price)
    """
    with connect_db(db_path) as conn:
        c = conn.cursor()
        c.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL
            )
        """)
        conn.commit()


def get_table_names(db_path: str = DB_PATH) -> List[str]:
    """
    Return a list of table names present in the database.

    Args:
        db_path (str): Path to the database file

    Returns:
        List[str]: Table names in the database
    """
    with connect_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
    return tables


# ------------------------------
# CRUD Operations
# ------------------------------


def insert_item(
    name: str,
    quantity: int,
    price: float,
    table: str = "inventory",
    db_path: str = DB_PATH,
) -> None:
    """
    Insert a new item into the specified table.

    Args:
        name (str): Item name
        quantity (int): Quantity available
        price (float): Price per unit
        table (str): Table to insert into (default 'inventory')
        db_path (str): Path to database file
    """
    with connect_db(db_path) as conn:
        conn.execute(
            f"INSERT INTO '{table}' (name, quantity, price) VALUES (?, ?, ?)",
            (name, int(quantity), float(price)),
        )
        conn.commit()


def fetch_items(
    table: str = "inventory", db_path: str = DB_PATH
) -> List[Tuple[int, str, int, float]]:
    """
    Fetch all items from the specified table.

    Args:
        table (str): Table to fetch from (default 'inventory')
        db_path (str): Path to database file

    Returns:
        list[tuple]: A list of (id, name, quantity, price) tuples
    """
    with connect_db(db_path) as conn:
        c = conn.cursor()
        c.execute(f"SELECT id, name, quantity, price FROM '{table}'")
        return c.fetchall()


def delete_item(item_id: int, table: str = "inventory", db_path: str = DB_PATH) -> None:
    """
    Delete an item by its ID from the specified table.

    Args:
        item_id (int): The ID of the item to delete
        table (str): Table to delete from (default 'inventory')
        db_path (str): Path to database file
    """
    with connect_db(db_path) as conn:
        conn.execute(f"DELETE FROM '{table}' WHERE id=?", (item_id,))
        conn.commit()


def update_item(
    item_id: int,
    name: str,
    quantity: int,
    price: float,
    table: str = "inventory",
    db_path: str = DB_PATH,
) -> None:
    """
    Update an existing item in the specified table.

    Args:
        item_id (int): The ID of the item to update
        name (str): The new name of the item
        quantity (int): The new quantity of the item
        price (float): The new price of the item
        table (str): Table to update (default 'inventory')
        db_path (str): Path to database file
    """
    with connect_db(db_path) as conn:
        conn.execute(
            f"UPDATE '{table}' SET name = ?, quantity =

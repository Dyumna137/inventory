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
>>> insert_item("Keyboard", 5, 1200.50, "inventory", "db/inventory.db")
>>> print(fetch_items("inventory", "db/inventory.db"))
[("Keyboard", 5, 1200.5)]
"""

import sqlite3
from typing import List, Tuple
from core.config import DB_NAME
from sqlalchemy import create_engine
import pandas as pd

# ------------------------------
# Generic Utilities
# ------------------------------


def connect_db(db_path: str = DB_NAME) -> sqlite3.Connection:
    """
    Establish a connection to the SQLite database.

    Args:
        db_path (str): Path to the database file

    Returns:
        sqlite3.Connection: Database connection object
    """
    return sqlite3.connect(db_path)


def init_db(db_path: str = DB_NAME, table_name: str = "inventory") -> None:
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


def get_table_names(db_path: str = DB_NAME) -> List[str]:
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
    db_path: str = DB_NAME,
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
            (name, quantity, price),
        )
        conn.commit()


def fetch_items(
    table: str = "inventory", db_path: str = DB_NAME
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


def delete_item(item_id: int, table: str = "inventory", db_path: str = DB_NAME) -> None:
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
    db_path: str = DB_NAME,
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
            f"UPDATE '{table}' SET name = ?, quantity = ?, price = ? WHERE id = ?",
            (name, quantity, price, item_id),
        )
        conn.commit()


def get_column_names(table: str, db_path: str = DB_NAME) -> list:
    """
    Get the list of column names for a given table.
    """
    with connect_db(db_path) as conn:
        c = conn.cursor()
        c.execute(f"PRAGMA table_info('{table}')")
        return [row[1] for row in c.fetchall()]


def fetch_table_rows(table: str, db_path: str = DB_NAME) -> list:
    """
    Fetch all rows from the given table, regardless of columns.
    Returns: List of tuples (row values).
    """
    with connect_db(db_path) as conn:
        c = conn.cursor()
        c.execute(f"SELECT * FROM '{table}'")
        return c.fetchall()


# ------------------------------
# Datasheet Handling
# ------------------------------


def save_dataframe(
    df: pd.DataFrame,
    table_name: str,
    db_path: str = DB_NAME,
    if_exists: str = "append",
) -> None:
    """
    Save a Pandas DataFrame into the SQLite database as a specified table.

    Args:
        df (pd.DataFrame): The DataFrame containing data
        table_name (str): Target table name
        db_path (str): Path to SQLite DB file (default: DB_NAME)
        if_exists (str): Behavior if table exists ("fail", "replace", "append")

    Notes:
        - Uses SQLAlchemy engine for robust dtype handling
        - Caller is responsible for schema consistency
    """
    engine = create_engine(f"sqlite:///{db_path}")
    df.to_sql(table_name, engine, if_exists=if_exists, index=False)


def import_datasheet(
    filepath: str, table_name: str = "inventory", db_path: str = DB_NAME
) -> None:
    """
    Import a datasheet (CSV/Excel) into the database as a specified table.

    Args:
        filepath (str): Path to the datasheet file
        table_name (str): Target table name (default: "inventory")
        db_path (str): Path to database

    Supported formats:
        - .csv
        - .xls / .xlsx
    """
    if filepath.endswith(".csv"):
        df = pd.read_csv(filepath)
    elif filepath.endswith((".xls", ".xlsx")):
        df = pd.read_excel(filepath)
    else:
        raise ValueError("Unsupported file format. Use CSV or Excel.")

    save_dataframe(df, table_name, db_path=db_path)

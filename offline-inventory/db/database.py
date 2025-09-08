"""
database.py
===========

Database persistence layer for the inventory project.

This module provides:
- Core inventory database schema initialization
- CRUD operations (insert, fetch, delete)
- Helper for saving Pandas DataFrames to the database (useful for datasheet imports)

Dependencies:
- sqlite3 (standard library)
- SQLAlchemy (for flexible Pandas-to-SQL handling)
- Pandas (for dataframe operations)

Typical usage:
--------------
>>> from db.database import init_db, insert_item, fetch_items
>>> init_db()
>>> insert_item("Keyboard", 5, 1200.50)
>>> print(fetch_items())
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


def connect_db() -> sqlite3.Connection:
    """
    Establish a connection to the SQLite database.

    Returns:
        sqlite3.Connection: Database connection object
    """
    return sqlite3.connect(DB_NAME)


def init_db() -> None:
    """
    Initialize the database with the required tables if not already present.

    Creates:
        - inventory (id, name, quantity, price)
    """
    with connect_db() as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL
            )
        """)
        conn.commit()


# ------------------------------
# CRUD Operations
# ------------------------------


def insert_item(name: str, quantity: int, price: float) -> None:
    """
    Insert a new item into the inventory table.

    Args:
        name (str): Item name
        quantity (int): Quantity available
        price (float): Price per unit
    """
    with connect_db() as conn:
        conn.execute(
            "INSERT INTO inventory (name, quantity, price) VALUES (?, ?, ?)",
            (name, quantity, price),
        )
        conn.commit()


def fetch_items() -> List[Tuple[str, int, float]]:
    """
    Fetch all items from the inventory table.

    Returns:
        list[tuple]: A list of (name, quantity, price) tuples
    """
    with connect_db() as conn:
        c = conn.cursor()
        c.execute("SELECT name, quantity, price FROM inventory")
        return c.fetchall()


def delete_item(name: str) -> None:
    """
    Delete an item by name from the inventory.

    Args:
        name (str): The name of the item to delete
    """
    with connect_db() as conn:
        conn.execute("DELETE FROM inventory WHERE name=?", (name,))
        conn.commit()


# ------------------------------
# Datasheet Handling
# ------------------------------


def save_dataframe(
    df: pd.DataFrame,
    table_name: str,
    db_path: str = "db/inventory.db",
    if_exists: str = "append",
) -> None:
    """
    Save a Pandas DataFrame into the SQLite database.

    Args:
        df (pd.DataFrame): The DataFrame containing data
        table_name (str): Target table name
        db_path (str): Path to SQLite DB file (default: "db/inventory.db")
        if_exists (str): Behavior if table exists ("fail", "replace", "append")

    Notes:
        - Uses SQLAlchemy engine for robust dtype handling
        - Caller is responsible for schema consistency
    """
    engine = create_engine(f"sqlite:///{db_path}")
    df.to_sql(table_name, engine, if_exists=if_exists, index=False)


def import_datasheet(filepath: str, table_name: str = "inventory") -> None:
    """
    Import a datasheet (CSV/Excel) into the database.

    Args:
        filepath (str): Path to the datasheet file
        table_name (str): Target table name (default: "inventory")

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

    save_dataframe(df, table_name)

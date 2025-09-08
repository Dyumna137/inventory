# database.py (SQLite handler)
import sqlite3
from core.config import DB_NAME


def connect_db():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = connect_db()
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
    conn.close()


def insert_item(name, quantity, price):
    conn = connect_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO inventory (name, quantity, price) VALUES (?, ?, ?)",
        (name, quantity, price),
    )
    conn.commit()
    conn.close()


def fetch_items():
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT name, quantity, price FROM inventory")
    items = c.fetchall()
    conn.close()
    return items


def delete_item(name):
    conn = connect_db()
    c = conn.cursor()
    c.execute("DELETE FROM inventory WHERE name=?", (name,))
    conn.commit()
    conn.close()

"""
Simple Database Module
=====================

Lightweight database layer for the flexible inventory system.
Uses sqlite3 for portable storage.
"""

import sqlite3
import json
from typing import List, Dict, Any, Optional
from pathlib import Path


class Database:
    """Simple database wrapper for inventory management."""
    
    def __init__(self, db_path: str = "data/inventory.db"):
        """Initialize database connection."""
        self.db_path = db_path
        
        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_tables()
    
    def _init_tables(self):
        """Create the items table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    data TEXT NOT NULL
                )
            """)
            conn.commit()
    
    def save_item(self, item_dict: Dict[str, Any]) -> bool:
        """Save an item to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO items (id, created_at, updated_at, data)
                    VALUES (?, ?, ?, ?)
                """, (
                    item_dict['id'],
                    item_dict['created_at'],
                    item_dict['updated_at'],
                    json.dumps(item_dict)
                ))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error saving item: {e}")
            return False
    
    def get_all_items(self) -> List[Dict[str, Any]]:
        """Get all items from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT data FROM items")
                rows = cursor.fetchall()
                
                items = []
                for row in rows:
                    try:
                        item_data = json.loads(row[0])
                        items.append(item_data)
                    except json.JSONDecodeError:
                        continue
                
                return items
        except Exception as e:
            print(f"Error loading items: {e}")
            return []
    
    def delete_item(self, item_id: str) -> bool:
        """Delete an item from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting item: {e}")
            return False
    
    def clear_items(self):
        """Clear all items from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM items")
                conn.commit()
        except Exception as e:
            print(f"Error clearing items: {e}")
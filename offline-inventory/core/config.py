"""
core.config
===========

Central configuration for the Offline Inventory project.

- DB_PATH: location of the sqlite file used by db.database
- SUPPORTED_EXTS: file extensions allowed for datasheet import dialogs
"""

from pathlib import Path

# Database path relative to project root (data/inventory.db)
DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = str(DATA_DIR / "inventory.db")

# Supported extensions for file dialogs (used by GUI)
SUPPORTED_EXTS = ("*.csv", "*.xls", "*.xlsx", "*.pdf", "*.txt", "*.png", "*.jpg", "*.jpeg")

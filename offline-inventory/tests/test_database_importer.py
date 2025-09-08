
"""
test_database_importer.py
=========================

Quick test script to verify that the database importer works.
Run with:
    python tests/test_database_importer.py
"""

import os
import pandas as pd
from db.database import init_db, import_datasheet, fetch_items

# Step 1: Setup a temporary test datasheet
sample_file = "tests/sample_inventory.csv"

df = pd.DataFrame({
    "name": ["Keyboard", "Mouse", "Monitor"],
    "quantity": [5, 10, 3],
    "price": [1200.5, 450.0, 8000.0]
})

df.to_csv(sample_file, index=False)
print(f"[INFO] Sample datasheet created: {sample_file}")

# Step 2: Initialize the DB (ensures table exists)
init_db()

# Step 3: Import the datasheet into DB
print("[INFO] Importing datasheet into database...")
import_datasheet(sample_file)

# Step 4: Fetch items to verify
items = fetch_items()
print("[INFO] Items fetched from DB:")
for item in items:
    print("   ", item)

# Step 5: Cleanup test file
os.remove(sample_file)
print("[INFO] Test datasheet removed.")



"""
Expected OutPut
[INFO] Sample datasheet created: tests/sample_inventory.csv
[INFO] Importing datasheet into database...
[INFO] Items fetched from DB:
    ('Keyboard', 5, 1200.5)
    ('Mouse', 10, 450.0)
    ('Monitor', 3, 8000.0)
[INFO] Test datasheet removed.

"""

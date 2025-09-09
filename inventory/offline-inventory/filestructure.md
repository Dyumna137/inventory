```
inventory_project/
│── core/
│   ├── inventory.py   # Defines the Inventory class, handles items
│   ├── logic.py       # Business logic (add/remove/search/update)
│   ├── config.py      # Configuration (DB path, settings)
│   │
│── ui/
│   └── gui.py         # GUI code (Tkinter for now, can swap later)
│
│── db/
│   ├── database.py    # SQLite3 database operations
│   └── inventory.db      # <-- Your actual database file lives here 
│── tests/
│   └── test_inventory.py  # Unit tests
│
│── README.md
│── requirements.txt

```

Work-flow
⚙️ Workflow of Modular Inventory System
1. Database Layer (data storage)

` db_manager.py ` handles all the database operations.

Example:
add_item(name, qty, price) → Inserts into DB.
get_items() → Returns all items.
delete_item(item_id) → Removes item.

👉 This layer doesn’t care about GUI or CLI. It just stores & retrieves.
2. Logic Layer (business rules)
` inventory.py ` defines the Item class and InventoryManager.

Example:
Item("Sword", 2, 100) → Creates an item object. Eventhen name is Inventory for simple understanding name is Item.
InventoryManager.add_item(item) → Saves it (calls db_manager under the hood).
This layer ensures consistency (e.g., no negative quantities).

👉 This layer knows about DB, but not about GUI.
3. Interface Layer (GUI / CLI / API)
` gui.py ` provides buttons, forms, and lists.

Example:
User clicks Add Item → GUI collects input → calls InventoryManager.add_item().
GUI just displays results; logic is still handled in InventoryManager.

👉 This layer can be swapped. (You can start with Tkinter, later switch to Kivy or PyQt without rewriting backend.)
4. Launcher (optional)
run_gui.py → only launches the GUI.
You don’t need a big main.py, just entry points.

Example:
python run_gui.py

🔄 Flow Example: Adding a Sword
User clicks "Add Item" in GUI.
GUI collects: Sword, qty=2, price=100.
GUI calls → InventoryManager.add_item(Item("Sword", 2, 100)).
InventoryManager validates → sends to DB via db_manager.insert_item().
DB stores in SQLite.
GUI refreshes list → shows Sword added.

So basically:
User → GUI → Logic (InventoryManager + Item) → DB → back to GUI.


⚙️ How It Works (Workflow)

Config (` config.py `) → Holds global settings (e.g., database name, table structure).
Database (` database.py `) → Handles direct interaction with SQLite (create tables, insert, fetch).
Inventory (` inventory.py `) → Represents items and categories as Python objects.
Logic (` logic.py `) → Contains business rules (add item, remove, update quantity, search).
UI (` gui.py `) → User interface that calls functions from logic.py.
Tests (` test_inventory.py `) → Ensures core features (add/remove/search) work correctly.

🚀 Features
Add new items (with name, category, quantity, price).
Update item details.
Delete items.
Search inventory.
GUI support (Tkinter).
SQLite storage for persistence.


Great question! Here’s how your GUI decides **which database to show and use**:

---

## **How Database Is Chosen in Your Code**

### 1. **Database Location Is Set in `db/database.py`**
- The connection to the database is made by the function:

  ```python
  def connect_db() -> sqlite3.Connection:
      return sqlite3.connect(DB_NAME)
  ```
- `DB_NAME` is imported from `core/config.py`:

  ```python
  from core.config import DB_NAME
  ```

- **So the actual database file (e.g., `"db/inventory.db"`) is determined by the value of `DB_NAME` in your `core/config.py` file.**

---

### 2. **All GUI Actions Use This Database**
- The GUI calls functions like `database.fetch_items()`, `database.insert_item()`, etc.
- **All these functions interact with the database file specified by `DB_NAME`.**

---

### 3. **Importing Datasheets**
- When you use the "Import Datasheet" button, it calls:

  ```python
  tables = datasheet_importer.ingest_file(file_path)
  for name, df in tables:
      save_dataframe(df, datasheet_importer.slugify(name))
  ```
- `save_dataframe` by default also writes to the database defined in `core/config.py` (unless overridden).

---

## **Summary Table**

| Function in `gui.py`            | Calls...                | Uses Database...            |
|----------------------------------|-------------------------|-----------------------------|
| `refresh_listbox`, `add_item`, etc. | `database.py` functions | Set by `DB_NAME` in config  |
| Import Datasheet                 | `save_dataframe`        | Set by `DB_NAME` in config  |

---

## **How to Change Which Database Is Used/Shown**
- **Edit `DB_NAME` in `core/config.py`.**  
  Example:
  ```python
  DB_NAME = "db/inventory.db"
  # Or: DB_NAME = "inventory/offline-inventory/db/inventory.db"
  ```
- Restart your GUI app.

---

**In summary:**  
The database your GUI shows and uses is determined by the value of `DB_NAME` in your `core/config.py`.  
If you change that value, your GUI will use a different database file.

Let me know if you want to see the contents of your config file, or need to support multiple database paths!

# gui_documented.py
# =================
# Annotated copy of your Tkinter GUI for the Offline Inventory Management app.
#
# Purpose:
# - Add clear, actionable comments (Sphinx-style where useful) to explain each
#   function's responsibility, assumptions, integration points, failure modes,
#   and UI behaviour. This file does not change program logic — only adds
#   explanatory comments to help future-you (or other contributors).
#
# How to use:
# - This is a documentation overlay. It is safe to replace your original gui.py
#   with this file if you want commentary baked in. If you prefer keeping the
#   original file unchanged, use this as a reference.
#
# Notes:
# - All comments are prefixed with '#' and do not alter runtime behaviour.
# - Where helpful, I call out GUI integration points for process_and_import and
#   preview_and_analyze (from core.logic) and database interactions (db.database).

"""
GUI Documentation Summary
-------------------------
This module implements the main Tkinter GUI for the Offline Inventory Management
application. It provides the following responsibilities:

- Database selection and table selection UI
- CRUD operations for inventory-like tables (id, name, quantity, price)
- Generic preview for non-inventory tables
- Import datasheet flow (via core.datasheet_importer and db.save_dataframe)

Important integration points:
- `database.get_table_names`, `database.get_column_names`, `database.fetch_table_rows`
  are used to query schema and rows for currently selected table.
- `datasheet_importer.ingest_file` and `save_dataframe` are used for datasheet
  import and persistence.

Expected file location/package layout:
- db/database.py (contains persistence helpers)
- core/datasheet_importer.py (parsers for CSV/Excel/PDF/Image)

This annotated copy keeps the original logic exactly but provides explanation for
each function's intent, assumptions, and failure modes.
"""

import tkinter as tk
from tkinter import messagebox, ttk, font, filedialog
from db import database
from core import datasheet_importer
from db.database import save_dataframe

# --- GLOBAL STATE ---
# Explanation:
# - items: local cache of rows for the active table; each element should be
#   a tuple matching the SQL SELECT * order (id, name, quantity, price) for
#   inventory tables, or generic tuples for other tables.
# - active_db_path: string path to currently selected sqlite database file.
# - active_table_name: currently selected table name within active_db_path.
items = []  # Stores current table's items in a local list
active_db_path = None  # Path to currently selected database file
active_table_name = None  # Name of currently selected table


def choose_database(root, table_var, table_dropdown, listbox):
    """
    Open file dialog to choose a database file and refresh UI state.

    Side effects:
    - sets global active_db_path and active_table_name
    - updates window title to include db path
    - refreshes table_dropdown values and the main listbox view

    Parameters
    ----------
    root : tk.Tk
        The main Tk root window (used to set title)
    table_var : tk.StringVar
        Bound to the table dropdown so we can set the selected value
    table_dropdown : ttk.Combobox
        Dropdown widget that will be updated with available tables
    listbox : tk.Listbox
        The main listbox used to display rows
    """
    global active_db_path, active_table_name
    db_path = filedialog.askopenfilename(
        title="Select Database File",
        filetypes=[("SQLite DB", "*.db"), ("All Files", "*.*")],
    )
    if db_path:
        active_db_path = db_path
        root.title(f"Offline Inventory Management - {db_path}")
        # Query table names from selected DB and populate dropdown
        tables = database.get_table_names(db_path)
        table_dropdown["values"] = tables
        if tables:
            active_table_name = tables[0]
            table_var.set(active_table_name)
        else:
            active_table_name = None
            table_var.set("")
        refresh_listbox(listbox)


def refresh_table_dropdown(table_var, table_dropdown, listbox):
    """
    Refresh the table dropdown values from the currently selected database.

    This is useful after importing datasheets or when the database file's schema
    may have changed. The function is a no-op if no database is currently chosen.
    """
    global active_db_path, active_table_name
    if not active_db_path:
        return
    tables = database.get_table_names(active_db_path)
    table_dropdown["values"] = tables
    if tables:
        # Default to first table found
        active_table_name = tables[0]
        table_var.set(active_table_name)
    else:
        active_table_name = None
        table_var.set("")
    refresh_listbox(listbox)


def on_table_change(event, listbox, table_var):
    """
    Event handler for when the user selects a different table in the table dropdown.

    Behavior:
    - sets the global active_table_name to the new selection
    - repopulates the listbox with rows from the selected table
    """
    global active_table_name
    active_table_name = table_var.get()
    refresh_listbox(listbox)


# --- Modern UI Enhancements ---
# This helper centralizes style configuration so the UI remains consistent.
# It modifies ttk.Style theme and fonts; safe to call once on startup.
def setup_styles():
    """
    Configure ttk styles, fonts and colors used across the application.

    Notes:
    - The function uses 'clam' theme for a clean look. Other themes may be used
      depending on target platforms; the visual result can vary between OSes.
    - Fonts are set to Segoe UI which is common on Windows; on other systems
      fallback fonts will be used if Segoe UI is unavailable.
    """
    style = ttk.Style()
    style.theme_use("clam")  # A clean, modern theme

    # Define colors
    BG_COLOR = "#2E2E2E"
    FG_COLOR = "#FFFFFF"
    PRIMARY_COLOR = "#4A90E2"
    SECONDARY_COLOR = "#50E3C2"
    ENTRY_BG = "#3A3A3A"
    BUTTON_COLOR = "#444444"
    BUTTON_HOVER = "#555555"

    # Define fonts
    default_font = font.nametofont("TkDefaultFont")
    default_font.configure(family="Segoe UI", size=10)
    entry_font = font.Font(family="Segoe UI", size=11)

    # Configure styles for widgets
    style.configure(".", background=BG_COLOR,
                    foreground=FG_COLOR, font=default_font)
    style.configure("TFrame", background=BG_COLOR)
    style.configure("TLabel", background=BG_COLOR,
                    foreground=FG_COLOR, padding=(5, 5))
    style.configure(
        "TEntry",
        fieldbackground=ENTRY_BG,
        foreground=FG_COLOR,
        insertcolor=FG_COLOR,
        borderwidth=0,
        font=entry_font,
    )
    style.map("TEntry", fieldbackground=[("focus", "#444444")])
    style.configure(
        "TButton",
        background=BUTTON_COLOR,
        foreground=FG_COLOR,
        borderwidth=1,
        padding=(10, 5),
        font=("Segoe UI", 10, "bold"),
    )
    style.map(
        "TButton",
        background=[("active", BUTTON_HOVER), ("!disabled", BUTTON_COLOR)],
        foreground=[("active", FG_COLOR)],
    )
    style.configure(
        "TListbox",
        background=ENTRY_BG,
        foreground=FG_COLOR,
        selectbackground=PRIMARY_COLOR,
        selectforeground=FG_COLOR,
        borderwidth=0,
        highlightthickness=0,
    )


# --- Core Application Logic ---
# The refresh_listbox function is the primary place where table rows are
# transformed into human-friendly strings for display in the listbox.
def refresh_listbox(listbox):
    """
    Repopulate the main listbox with all rows of the currently selected table.

    Behavior:
    - If active table matches the inventory schema (id, name, quantity, price),
      it shows "Name (xQuantity) - $Price" style strings.
    - For other tables, it shows a generic CSV-like preview (first 3 columns)

    This function also updates the global 'items' cache used by selection
    handlers (on_item_select, delete_item, etc.).
    """
    global items, active_db_path, active_table_name
    listbox.delete(0, tk.END)
    if not active_db_path or not active_table_name:
        return
    # Get column names for this table
    cols = database.get_column_names(active_table_name, active_db_path)
    items = database.fetch_table_rows(active_table_name, active_db_path)
    if cols == ["id", "name", "quantity", "price"]:
        # Inventory-style table: show friendly labels
        for item in items:
            listbox.insert(tk.END, f"{item[1]} (x{item[2]}) - ${item[3]:.2f}")
    else:
        # Generic preview: join first 3 columns; this prevents the UI from
        # crashing when tables have different schema
        for item in items:
            txt = ", ".join(str(val) for val in item[:3])
            listbox.insert(tk.END, txt)


def add_item(name_entry, quantity_entry, price_entry, listbox):
    """
    Add a new item to the current table after validating the inventory schema.

    Important checks:
    - Only allowed for tables that match the exact inventory schema
    - Ensures all fields are present and have valid types (int for quantity,
      float for price) before calling database.insert_item

    UI effects:
    - On success, refreshes the listbox and clears input entries
    - On failure, shows a messagebox with a helpful error message
    """
    global active_db_path, active_table_name
    cols = database.get_column_names(active_table_name, active_db_path)
    if cols != ["id", "name", "quantity", "price"]:
        messagebox.showerror(
            "Error", "Cannot add/update/delete items in a non-inventory table."
        )
        return
    name = name_entry.get()
    quantity = quantity_entry.get()
    price = price_entry.get()

    if not name or not quantity or not price:
        messagebox.showerror("Error", "All fields are required.")
        return

    try:
        database.insert_item(
            name, int(quantity), float(
                price), active_table_name, active_db_path
        )
        refresh_listbox(listbox)
        clear_entries(name_entry, quantity_entry, price_entry)
    except Exception:
        # Intentionally broad catch: any unexpected conversion or DB error
        # is reported to the user as invalid input. For debugging, inspect
        # the DB layer or enable logging to see the underlying exception.
        messagebox.showerror(
            "Error",
            "Invalid input: Quantity must be an integer and Price must be a number.",
        )


def update_item(name_entry, quantity_entry, price_entry, listbox):
    """
    Update the currently selected item in the listbox.

    Preconditions:
    - Active table must match inventory schema
    - An item must be selected in the listbox

    Behavior:
    - Validates inputs and calls database.update_item
    - Refreshes the listbox and clears fields on success
    """
    global items, active_db_path, active_table_name
    cols = database.get_column_names(active_table_name, active_db_path)
    if cols != ["id", "name", "quantity", "price"]:
        messagebox.showerror(
            "Error", "Cannot add/update/delete items in a non-inventory table."
        )
        return
    selected_item_index = listbox.curselection()
    if not selected_item_index:
        messagebox.showerror("Error", "Please select an item to update.")
        return

    selected_item_id = items[selected_item_index[0]][0]
    name = name_entry.get()
    quantity = quantity_entry.get()
    price = price_entry.get()

    if not name or not quantity or not price:
        messagebox.showerror("Error", "All fields are required.")
        return

    try:
        database.update_item(
            selected_item_id,
            name,
            int(quantity),
            float(price),
            active_table_name,
            active_db_path,
        )
        refresh_listbox(listbox)
        clear_entries(name_entry, quantity_entry, price_entry)
    except Exception:
        messagebox.showerror(
            "Error",
            "Invalid input: Quantity must be an integer and Price must be a number.",
        )


def delete_item(listbox):
    """
    Delete the selected item from the active inventory table.

    Safety checks:
    - Only allowed for inventory schema tables (protects against accidental
      deletion of non-inventory tables)
    - Requires a listbox selection

    After deletion, the listbox is refreshed to reflect current DB state.
    """
    global items, active_db_path, active_table_name
    cols = database.get_column_names(active_table_name, active_db_path)
    if cols != ["id", "name", "quantity", "price"]:
        messagebox.showerror(
            "Error", "Cannot add/update/delete items in a non-inventory table."
        )
        return
    selected_item_index = listbox.curselection()
    if not selected_item_index:
        messagebox.showerror("Error", "Please select an item to delete.")
        return

    selected_item_id = items[selected_item_index[0]][0]
    database.delete_item(selected_item_id, active_table_name, active_db_path)
    refresh_listbox(listbox)


def clear_entries(*entries):
    """
    Clear a list of Tk Entry widgets. Useful after add/update/delete
    operations to reset the input fields.
    """
    for entry in entries:
        entry.delete(0, tk.END)


def on_item_select(event, name_entry, quantity_entry, price_entry):
    """
    Populate the entry fields with data from the selected listbox item.

    Notes:
    - Uses the global `items` list for mapping index -> DB row tuple
    - Ensures entries are cleared before inserting to avoid cursor artifacts
    - Guarded against empty selection (user may click blank area)
    """
    global items
    selected_item_index = event.widget.curselection()
    if not selected_item_index:
        return

    selected_item = items[selected_item_index[0]]
    clear_entries(name_entry, quantity_entry, price_entry)
    name_entry.insert(0, selected_item[1])
    quantity_entry.insert(0, selected_item[2])
    price_entry.insert(0, f"{selected_item[3]:.2f}")


def import_datasheet(table_var, table_dropdown, listbox):
    """
    GUI handler for importing a datasheet file and saving parsed tables to DB.

    Flow:
    - Ensure a database is selected
    - Ask user to choose a datasheet file
    - Use datasheet_importer.ingest_file to parse the file into DataFrames
    - For each parsed table, call save_dataframe to persist into the active DB
    - Refresh the table dropdown so newly imported tables appear

    Error handling:
    - Any exception during parsing or saving is shown to the user

    UX considerations (future improvements):
    - Present a preview modal to the user showing parsed columns/rows and
      validation warnings (use core.logic.preview_and_analyze for richer data)
    - Allow the user to rename the table before writing to DB
    """
    global active_db_path
    if not active_db_path:
        messagebox.showerror("Error", "Please choose a database first.")
        return
    file_path = filedialog.askopenfilename(
        title="Select Datasheet",
        filetypes=[
            ("Supported files", "*.csv *.xls *.xlsx *.pdf *.txt *.png *.jpg *.jpeg")
        ],
    )
    if not file_path:
        return

    try:
        tables = datasheet_importer.ingest_file(file_path)
        for name, df in tables:
            # Save DataFrame into active DB. The slugify step ensures valid table
            # names in sqlite. `save_dataframe` uses SQLAlchemy to handle types.
            save_dataframe(df, datasheet_importer.slugify(
                name), db_path=active_db_path)
        messagebox.showinfo(
            "Success", f"Imported {len(tables)} table(s) from {file_path}"
        )
        refresh_table_dropdown(table_var, table_dropdown, listbox)
    except Exception as e:
        # Propagate a helpful error message to the user; developers can inspect
        # the exception in logs for debugging.
        messagebox.showerror("Error", str(e))


# --- GUI Setup ---
# The `run_gui` function composes the whole UI. It is safe to call multiple
# times in dev but typically called only when __main__.
def run_gui():
    """
    Initialize and run the Tkinter GUI application.

    Responsibilities:
    - Create main window and frames
    - Set up styling (setup_styles)
    - Build widgets: listbox, input entries, buttons, dropdowns
    - Wire event handlers and mainloop

    Notes on structure:
    - The GUI is split into logical sections: top frame (db/table), main listbox,
      input frame, and button frame — this keeps layout predictable and easy to
    modify later.
    """
    global active_db_path, active_table_name
    root = tk.Tk()
    root.title("Offline Inventory Management")
    root.geometry("650x550")
    root.configure(bg="#2E2E2E")

    setup_styles()

    # --- Top Frame: Database and Table Selection ---
    top_frame = ttk.Frame(root, padding="5")
    top_frame.pack(fill="x")

    # Table selection variable and dropdown
    table_var = tk.StringVar()
    table_dropdown = ttk.Combobox(
        top_frame, textvariable=table_var, state="readonly", width=25
    )
    table_dropdown.pack(side="right", padx=(5, 0))
    ttk.Label(top_frame, text="Table:").pack(side="right", padx=(5, 2))

    # --- Listbox defined before Choose Database Button (fixes use prior to assignment) ---
    main_frame = ttk.Frame(root, padding="10")
    main_frame.pack(expand=True, fill="both")

    listbox_frame = ttk.Frame(main_frame)
    listbox_frame.pack(expand=True, fill="both")

    listbox = tk.Listbox(
        listbox_frame,
        width=60,
        height=15,
        background="#3A3A3A",
        foreground="#FFFFFF",
        selectbackground="#4A90E2",
        selectforeground="#FFFFFF",
        borderwidth=0,
        highlightthickness=0,
        font=("Segoe UI", 11),
    )
    listbox.pack(side="left", expand=True, fill="both")

    scrollbar = ttk.Scrollbar(
        listbox_frame, orient="vertical", command=listbox.yview)
    scrollbar.pack(side="right", fill="y")
    listbox.config(yscrollcommand=scrollbar.set)

    # Choose Database Button
    choose_db_btn = ttk.Button(
        top_frame,
        text="Choose Database",
        command=lambda: choose_database(
            root, table_var, table_dropdown, listbox),
    )
    choose_db_btn.pack(side="left", padx=(5, 10))

    # Table dropdown event binding
    table_dropdown.bind(
        "<<ComboboxSelected>>", lambda event: on_table_change(
            event, listbox, table_var)
    )

    # --- Input Frame ---
    input_frame = ttk.Frame(main_frame)
    input_frame.pack(fill="x", pady=(0, 10))
    input_frame.columnconfigure(1, weight=1)

    ttk.Label(input_frame, text="Name:").grid(
        row=0, column=0, sticky="w", padx=(0, 5))
    name_entry = ttk.Entry(input_frame)
    name_entry.grid(row=0, column=1, sticky="ew")

    ttk.Label(input_frame, text="Quantity:").grid(
        row=1, column=0, sticky="w", padx=(0, 5)
    )
    quantity_entry = ttk.Entry(input_frame)
    quantity_entry.grid(row=1, column=1, sticky="ew")

    ttk.Label(input_frame, text="Price:").grid(
        row=2, column=0, sticky="w", padx=(0, 5))
    price_entry = ttk.Entry(input_frame)
    price_entry.grid(row=2, column=1, sticky="ew")

    for widget in input_frame.winfo_children():
        widget.grid_configure(pady=5)

    # --- Button Frame ---
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill="x", pady=10)
    button_frame.columnconfigure((0, 1, 2, 3, 4), weight=1)

    ttk.Button(
        button_frame,
        text="Add Item",
        command=lambda: add_item(
            name_entry, quantity_entry, price_entry, listbox),
    ).grid(row=0, column=0, sticky="ew", padx=5)

    ttk.Button(
        button_frame,
        text="Update Item",
        command=lambda: update_item(
            name_entry, quantity_entry, price_entry, listbox),
    ).grid(row=0, column=1, sticky="ew", padx=5)

    ttk.Button(
        button_frame, text="Delete Item", command=lambda: delete_item(listbox)
    ).grid(row=0, column=2, sticky="ew", padx=5)

    ttk.Button(
        button_frame,
        text="Clear Entries",
        command=lambda: clear_entries(name_entry, quantity_entry, price_entry),
    ).grid(row=0, column=3, sticky="ew", padx=5)

    ttk.Button(
        button_frame,
        text="Import Datasheet",
        command=lambda: import_datasheet(table_var, table_dropdown, listbox),
    ).grid(row=0, column=4, sticky="ew", padx=5)

    listbox.bind(
        "<<ListboxSelect>>",
        lambda event: on_item_select(
            event, name_entry, quantity_entry, price_entry),
    )

    root.mainloop()


if __name__ == "__main__":
    run_gui()

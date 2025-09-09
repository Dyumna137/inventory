"""
Inventory Management GUI (Tkinter)
==================================
This GUI allows users to manage inventory items, import datasheets, and switch between multiple databases and tables.
- Choose a database file (.db) to work with.
- Choose a table (inventory/datasheet) within the selected database.
- Perform CRUD operations (Add, Update, Delete) on items in the chosen table.
- Import datasheets as new tables into the selected database.

Author: Dyumna137
"""

import tkinter as tk
from tkinter import messagebox, ttk, font, filedialog
from db import database
from core import datasheet_importer
from db.database import save_dataframe

# --- GLOBAL STATE ---
items = []  # Stores current table's items in a local list
active_db_path = None  # Path to currently selected database file
active_table_name = None  # Name of currently selected table


def choose_database(root, table_var, table_dropdown, listbox):
    """
    Opens a file dialog for the user to select a database (.db) file.
    Updates the active database path and refreshes table dropdown and item list.
    """
    global active_db_path, active_table_name
    db_path = filedialog.askopenfilename(
        title="Select Database File",
        filetypes=[("SQLite DB", "*.db"), ("All Files", "*.*")],
    )
    if db_path:
        active_db_path = db_path
        root.title(f"Offline Inventory Management - {db_path}")
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
    Loads the list of tables from the current database and updates the table selection dropdown.
    Sets the active table to the first found (if any) and refreshes the item list.
    """
    global active_db_path, active_table_name
    if not active_db_path:
        return
    tables = database.get_table_names(active_db_path)
    table_dropdown["values"] = tables
    if tables:
        active_table_name = tables[0]
        table_var.set(active_table_name)
    else:
        active_table_name = None
        table_var.set("")
    refresh_listbox(listbox)


def on_table_change(event, listbox, table_var):
    """
    Triggered when the user selects a different table from the dropdown.
    Sets the active table name and refreshes the item list.
    """
    global active_table_name
    active_table_name = table_var.get()
    refresh_listbox(listbox)


# --- Modern UI Enhancements ---
def setup_styles():
    """
    Sets up modern styling for the application.
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
def refresh_listbox(listbox):
    """
    Clears and repopulates the listbox with all rows in the selected table.
    If table matches inventory schema, show inventory style.
    Otherwise, show generic preview.
    """
    global items, active_db_path, active_table_name
    listbox.delete(0, tk.END)
    if not active_db_path or not active_table_name:
        return
    # Get column names for this table
    cols = database.get_column_names(active_table_name, active_db_path)
    items = database.fetch_table_rows(active_table_name, active_db_path)
    if cols == ["id", "name", "quantity", "price"]:
        for item in items:
            listbox.insert(tk.END, f"{item[1]} (x{item[2]}) - ${item[3]:.2f}")
    else:
        # Show a summary for each row (first 3 columns)
        for item in items:
            txt = ", ".join(str(val) for val in item[:3])
            listbox.insert(tk.END, txt)


def add_item(name_entry, quantity_entry, price_entry, listbox):
    """
    Adds a new item to the current table in the active database after validation.
    Refreshes the listbox to show the new item.
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
        messagebox.showerror(
            "Error",
            "Invalid input: Quantity must be an integer and Price must be a number.",
        )


def update_item(name_entry, quantity_entry, price_entry, listbox):
    """
    Updates the selected item in the current table of the active database after validation.
    Refreshes the listbox to show the updated item.
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
    Deletes the selected item from the current table of the active database.
    Refreshes the listbox to remove the deleted item.
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
    Clears all given entry widgets (used after add/update/delete or when 'Clear Entries' is clicked).
    """
    for entry in entries:
        entry.delete(0, tk.END)


def on_item_select(event, name_entry, quantity_entry, price_entry):
    """
    Populates entry fields with data from the selected item in the listbox for easy editing/updating.
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
    Opens a file dialog for the user to select a datasheet file (CSV, Excel, PDF, TXT, image).
    Uses datasheet_importer to extract tables from the file and saves each as a new table in the active database.
    Refreshes the table dropdown to include newly imported tables.
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
            save_dataframe(df, datasheet_importer.slugify(
                name), db_path=active_db_path)
        messagebox.showinfo(
            "Success", f"Imported {len(tables)} table(s) from {file_path}"
        )
        refresh_table_dropdown(table_var, table_dropdown, listbox)
    except Exception as e:
        messagebox.showerror("Error", str(e))


# --- GUI Setup ---
def run_gui():
    """
    Initializes and runs the main GUI application.
    Sets up styles, widgets, and event bindings for database, table, and inventory management.
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

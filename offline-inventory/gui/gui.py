"""
Flexible Inventory GUI
=====================

Adaptive GUI for any inventory type - warehouse, retail, library, restaurant, etc.
The interface automatically adjusts based on the selected inventory configuration.

Author: [Your Team Name]
Version: 2.0.0
"""

import tkinter as tk
from tkinter import messagebox, ttk, font, filedialog
from decimal import Decimal
import os

from db.database import Database
from core.inventory import Item, Inventory
from core.config import get_inventory_fields, get_inventory_type, setup_inventory_type

# Global state
inventory = Inventory()
database = None
field_entries = {}  # Will store entry widgets for each field


def initialize_inventory_setup():
    """Setup inventory type if not already configured."""
    if not get_inventory_type():
        setup_inventory_type()

def choose_database(root, listbox):
    """Choose or create a database file for the inventory."""
    global database, inventory
    
    db_path = filedialog.askopenfilename(
        title="Select Database File",
        filetypes=[("SQLite DB", "*.db"), ("All Files", "*.*")],
    )
    
    if not db_path:
        # If no file selected, ask to create new one
        db_path = filedialog.asksaveasfilename(
            title="Create New Database",
            defaultextension=".db",
            filetypes=[("SQLite DB", "*.db"), ("All Files", "*.*")],
        )
    
    if db_path:
        database = Database(db_path)
        root.title(f"Flexible Inventory Management - {os.path.basename(db_path)}")
        load_inventory_from_database()
        refresh_listbox(listbox)

def load_inventory_from_database():
    """Load all items from the database into the inventory."""
    global inventory, database
    
    if not database:
        return
    
    inventory = Inventory()
    
    # Get all items from database
    items_data = database.get_all_items()
    
    for item_data in items_data:
        try:
            # Remove database-specific fields
            item_dict = dict(item_data)
            item_dict.pop('id', None)  # Let Item generate its own ID
            
            item = Item(**item_dict)
            inventory.add_item(item)
        except Exception as e:
            print(f"Error loading item: {e}")

def save_inventory_to_database():
    """Save all inventory items to the database."""
    global inventory, database
    
    if not database:
        return
    
    # Clear existing items and save current inventory
    database.clear_items()
    
    for item in inventory.get_all_items():
        database.save_item(item.to_dict())


def refresh_listbox(listbox):
    """Refresh the listbox with current inventory items."""
    global inventory
    
    listbox.delete(0, tk.END)
    
    if not inventory:
        return
    
    fields = get_inventory_fields()
    
    for item in inventory.get_all_items():
        # Create display string based on configured fields
        display_parts = []
        for field in fields[:3]:  # Show first 3 fields in list
            field_name = field["name"]
            value = item.data.get(field_name, "")
            display_parts.append(f"{field_name.title()}: {value}")
        
        listbox.insert(tk.END, " | ".join(display_parts))


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
    - If active table matches the inventory schema (id, name, Model, price),
      it shows "Name (xModel) - $Price" style strings.
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
    if cols == ["id", "name", "Model", "price"]:
        # Inventory-style table: show friendly labels
        for item in items:
            listbox.insert(tk.END, f"{item[1]} (x{item[2]}) - ${item[3]:.2f}")
    else:
        # Generic preview: join first 3 columns; this prevents the UI from
        # crashing when tables have different schema
        for item in items:
            txt = ", ".join(str(val) for val in item[:3])
            listbox.insert(tk.END, txt)


def add_item(listbox):
    """Add a new item to the inventory using field entries."""
    global inventory, field_entries
    
    if not field_entries:
        messagebox.showerror("Error", "No input fields available.")
        return
    
    # Collect data from all field entries
    item_data = {}
    fields = get_inventory_fields()
    
    for field in fields:
        field_name = field["name"]
        entry_widget = field_entries.get(field_name)
        
        if not entry_widget:
            continue
            
        value = entry_widget.get().strip()
        
        # Validate required fields
        if field["required"] and not value:
            messagebox.showerror("Error", f"Field '{field_name}' is required.")
            return
        
        # Type conversion
        if value:
            try:
                if field["type"] == "number":
                    value = int(value)
                elif field["type"] == "decimal":
                    value = Decimal(value)
            except ValueError:
                messagebox.showerror("Error", f"Invalid value for '{field_name}'. Expected {field['type']}.")
                return
        
        item_data[field_name] = value
    
    try:
        item = Item(**item_data)
        inventory.add_item(item)
        save_inventory_to_database()
        refresh_listbox(listbox)
        clear_entries()
        messagebox.showinfo("Success", "Item added successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to add item: {str(e)}")


def update_item(name_entry, Model_entry, price_entry, listbox):
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
    if cols != ["id", "name", "Model", "price"]:
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
    Model = Model_entry.get()
    price = price_entry.get()

    if not name or not Model or not price:
        messagebox.showerror("Error", "All fields are required.")
        return

    try:
        database.update_item(
            selected_item_id,
            name,
            int(Model),
            float(price),
            active_table_name,
            active_db_path,
        )
        refresh_listbox(listbox)
        clear_entries(name_entry, Model_entry, price_entry)
    except Exception:
        messagebox.showerror(
            "Error",
            "Invalid input: Model must be an integer and Price must be a number.",
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
    if cols != ["id", "name", "Model", "price"]:
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


def on_item_select(event, name_entry, Model_entry, price_entry):
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
    clear_entries(name_entry, Model_entry, price_entry)
    name_entry.insert(0, selected_item[1])
    Model_entry.insert(0, selected_item[2])
    price_entry.insert(0, f"{selected_item[3]:.2f}")





# --- GUI Setup ---
# The `run_gui` function composes the whole UI. It is safe to call multiple
# times in dev but typically called only when __main__.
def create_input_fields(parent_frame):
    """Create input fields based on current inventory configuration."""
    global field_entries
    
    fields = get_inventory_fields()
    field_entries = {}
    
    # Clear existing fields
    for widget in parent_frame.winfo_children():
        widget.destroy()
    
    parent_frame.columnconfigure(1, weight=1)
    
    for i, field in enumerate(fields):
        field_name = field["name"]
        label_text = field_name.replace("_", " ").title()
        
        # Add required indicator
        if field["required"]:
            label_text += " *"
        
        ttk.Label(parent_frame, text=f"{label_text}:").grid(
            row=i, column=0, sticky="w", padx=(0, 5), pady=5
        )
        
        entry = ttk.Entry(parent_frame)
        entry.grid(row=i, column=1, sticky="ew", pady=5)
        
        field_entries[field_name] = entry

def clear_entries():
    """Clear all field entries."""
    global field_entries
    for entry in field_entries.values():
        entry.delete(0, tk.END)

def update_item(listbox):
    """Update selected item in the inventory."""
    global inventory, field_entries
    
    selection = listbox.curselection()
    if not selection:
        messagebox.showerror("Error", "Please select an item to update.")
        return
    
    # Get the selected item
    items = inventory.get_all_items()
    if selection[0] >= len(items):
        messagebox.showerror("Error", "Invalid selection.")
        return
    
    selected_item = items[selection[0]]
    
    # Collect data from field entries
    item_data = {}
    fields = get_inventory_fields()
    
    for field in fields:
        field_name = field["name"]
        entry_widget = field_entries.get(field_name)
        
        if not entry_widget:
            continue
            
        value = entry_widget.get().strip()
        
        # Validate required fields
        if field["required"] and not value:
            messagebox.showerror("Error", f"Field '{field_name}' is required.")
            return
        
        # Type conversion
        if value:
            try:
                if field["type"] == "number":
                    value = int(value)
                elif field["type"] == "decimal":
                    value = Decimal(value)
            except ValueError:
                messagebox.showerror("Error", f"Invalid value for '{field_name}'. Expected {field['type']}.")
                return
        
        item_data[field_name] = value
    
    try:
        # Update the item's data
        for field_name, value in item_data.items():
            selected_item.update_field(field_name, value)
        
        save_inventory_to_database()
        refresh_listbox(listbox)
        clear_entries()
        messagebox.showinfo("Success", "Item updated successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to update item: {str(e)}")

def delete_item(listbox):
    """Delete selected item from inventory."""
    global inventory
    
    selection = listbox.curselection()
    if not selection:
        messagebox.showerror("Error", "Please select an item to delete.")
        return
    
    # Get selected item (this is simplified - in practice you'd need to track item IDs)
    items = inventory.get_all_items()
    if selection[0] < len(items):
        item = items[selection[0]]
        inventory.remove_item(item.id)
        save_inventory_to_database()
        refresh_listbox(listbox)
        messagebox.showinfo("Success", "Item deleted successfully!")

def search_items(query_entry, listbox):
    """Search items and update listbox."""
    global inventory
    
    query = query_entry.get().strip()
    if query:
        results = inventory.search_items(query)
        listbox.delete(0, tk.END)
        fields = get_inventory_fields()
        
        for item in results:
            display_parts = []
            for field in fields[:3]:
                field_name = field["name"]
                value = item.data.get(field_name, "")
                display_parts.append(f"{field_name.title()}: {value}")
            
            listbox.insert(tk.END, " | ".join(display_parts))
    else:
        refresh_listbox(listbox)

def on_item_select(event, listbox):
    """Populate input fields when an item is selected."""
    global inventory, field_entries
    
    selection = listbox.curselection()
    if not selection:
        return
    
    items = inventory.get_all_items()
    if selection[0] >= len(items):
        return
    
    selected_item = items[selection[0]]
    
    # Clear and populate fields
    clear_entries()
    
    for field_name, entry_widget in field_entries.items():
        value = selected_item.data.get(field_name, "")
        if value is not None:
            entry_widget.insert(0, str(value))

def run_gui():
    """Initialize and run the flexible inventory GUI."""
    global field_entries
    
    # Initialize inventory setup
    initialize_inventory_setup()
    
    root = tk.Tk()
    root.title("Flexible Inventory Management")
    root.geometry("800x600")
    root.configure(bg="#2E2E2E")
    
    setup_styles()
    
    # Main container
    main_frame = ttk.Frame(root, padding="10")
    main_frame.pack(expand=True, fill="both")
    
    # Top frame with database and inventory type info
    top_frame = ttk.Frame(main_frame)
    top_frame.pack(fill="x", pady=(0, 10))
    
    inventory_type = get_inventory_type()
    ttk.Label(top_frame, text=f"Inventory Type: {inventory_type.title()}").pack(side="left")
    
    ttk.Button(
        top_frame,
        text="Choose Database",
        command=lambda: choose_database(root, listbox)
    ).pack(side="right")
    
    # Search frame
    search_frame = ttk.Frame(main_frame)
    search_frame.pack(fill="x", pady=(0, 10))
    
    ttk.Label(search_frame, text="Search:").pack(side="left")
    search_entry = ttk.Entry(search_frame)
    search_entry.pack(side="left", fill="x", expand=True, padx=(5, 5))
    
    ttk.Button(
        search_frame,
        text="Search",
        command=lambda: search_items(search_entry, listbox)
    ).pack(side="right")
    
    # Main content area
    content_frame = ttk.Frame(main_frame)
    content_frame.pack(expand=True, fill="both")
    
    # Left side - Item list
    left_frame = ttk.Frame(content_frame)
    left_frame.pack(side="left", expand=True, fill="both", padx=(0, 10))
    
    ttk.Label(left_frame, text="Items").pack(anchor="w")
    
    listbox_frame = ttk.Frame(left_frame)
    listbox_frame.pack(expand=True, fill="both")
    
    listbox = tk.Listbox(
        listbox_frame,
        background="#3A3A3A",
        foreground="#FFFFFF",
        selectbackground="#4A90E2",
        selectforeground="#FFFFFF",
        borderwidth=0,
        highlightthickness=0,
        font=("Segoe UI", 10),
    )
    listbox.pack(side="left", expand=True, fill="both")
    
    scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=listbox.yview)
    scrollbar.pack(side="right", fill="y")
    listbox.config(yscrollcommand=scrollbar.set)
    
    # Right side - Input form
    right_frame = ttk.Frame(content_frame)
    right_frame.pack(side="right", fill="y")
    
    ttk.Label(right_frame, text="Item Details").pack(anchor="w", pady=(0, 10))
    
    # Input fields frame
    input_frame = ttk.Frame(right_frame)
    input_frame.pack(fill="both", expand=True)
    
    # Create input fields based on configuration
    create_input_fields(input_frame)
    
    # Buttons frame
    buttons_frame = ttk.Frame(right_frame)
    buttons_frame.pack(fill="x", pady=(10, 0))
    
    ttk.Button(
        buttons_frame,
        text="Add Item",
        command=lambda: add_item(listbox)
    ).pack(fill="x", pady=2)
    
    ttk.Button(
        buttons_frame,
        text="Update Item",
        command=lambda: update_item(listbox)
    ).pack(fill="x", pady=2)
    
    ttk.Button(
        buttons_frame,
        text="Delete Item",
        command=lambda: delete_item(listbox)
    ).pack(fill="x", pady=2)
    
    ttk.Button(
        buttons_frame,
        text="Clear Fields",
        command=clear_entries
    ).pack(fill="x", pady=2)
    
    # Bind item selection event
    listbox.bind(
        "<<ListboxSelect>>",
        lambda event: on_item_select(event, listbox)
    )
    
    root.mainloop()


if __name__ == "__main__":
    run_gui()

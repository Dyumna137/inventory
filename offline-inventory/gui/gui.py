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
from core.config import get_inventory_fields, get_inventory_type, setup_inventory_type, set_inventory_type, InventoryType, get_inventory_types
from core.datasheet_importer import ingest_file, get_supported_extensions

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
    
    # Start in the data directory where databases are stored
    from pathlib import Path
    data_dir = Path("data")
    initial_dir = str(data_dir) if data_dir.exists() else "."
    
    db_path = filedialog.askopenfilename(
        title="Select Database File",
        initialdir=initial_dir,
        filetypes=[("SQLite DB", "*.db"), ("All Files", "*.*")],
    )
    
    if not db_path:
        # If no file selected, ask to create new one
        db_path = filedialog.asksaveasfilename(
            title="Create New Database",
            initialdir=initial_dir,
            defaultextension=".db",
            filetypes=[("SQLite DB", "*.db"), ("All Files", "*.*")],
        )
    
    if db_path:
        try:
            database = Database(db_path)
            root.title(f"Inventory Management - {os.path.basename(db_path)}")
            load_inventory_from_database()
            refresh_listbox(listbox, filtered_items)
            messagebox.showinfo("Database", f"Database loaded successfully!\n{os.path.basename(db_path)}")
        except Exception as e:
            messagebox.showerror("Database Error", f"Error loading database:\n{str(e)}")

def load_inventory_from_database():
    """Load all items from the database into the inventory."""
    global inventory, database
    
    if not database:
        return
    
    inventory = Inventory()
    
    # Get all items from database
    items_data = database.get_all_items()
    print(f"Loading {len(items_data)} items from database...")
    
    for item_data in items_data:
        try:
            # Convert to dict and let Item constructor handle all fields properly
            item_dict = dict(item_data)
            print(f"Loading item data: {item_dict}")
            
            item = Item(**item_dict)
            inventory.add_item(item)
            # Get the appropriate display name based on inventory type
            display_name = (item.data.get('name') or 
                          item.data.get('title') or 
                          item.data.get('model') or 
                          f"Item {item.id[:8]}")
            print(f"Loaded item: {display_name} (ID: {item.id})")
        except Exception as e:
            print(f"Error loading item: {e}")
            print(f"Item data was: {item_data}")
            print(f"Item data: {item_data}")
    
    print(f"Successfully loaded {len(inventory.get_all_items())} items into inventory")
    
    # Update filtered_items to show all loaded items
    global filtered_items
    filtered_items = inventory.get_all_items()

def save_inventory_to_database():
    """Save all inventory items to the database safely."""
    global inventory, database, save_pending
    
    if not database or not inventory:
        return
    
    try:
        # Get all items to save
        items_data = [item.to_dict() for item in inventory.get_all_items()]
        
        if not items_data:
            print("Warning: No items to save to database")
            return
        
        # SAFE APPROACH: Save first, then clear old data
        # This prevents data loss if save fails
        print(f"Saving {len(items_data)} items to database...")
        
        # Clear and save in a transaction for atomicity
        database.clear_items()
        
        saved_count = 0
        for item_data in items_data:
            if database.save_item(item_data):
                saved_count += 1
            else:
                print(f"Failed to save item: {item_data.get('id', 'unknown')}")
        
        print(f"Successfully saved {saved_count}/{len(items_data)} items to database")
        save_pending = False
        
    except Exception as e:
        print(f"Error saving inventory to database: {e}")
        # Don't set save_pending = False if there was an error

def mark_for_save():
    """Mark that the inventory needs to be saved."""
    global save_pending
    save_pending = True


# Global variables for pagination and performance
current_page = 0
items_per_page = 100
filtered_items = []
save_pending = False

def refresh_listbox(table, items_to_show=None):
    """Refresh the table with current inventory items."""
    global inventory, filtered_items, current_page
    
    # Clear existing items
    for item in table.get_children():
        table.delete(item)
    
    if not inventory:
        return
    
    # Use provided items or get all items and update global filtered_items
    if items_to_show is not None:
        items = items_to_show
        filtered_items = items
    else:
        items = inventory.get_all_items()
        filtered_items = items
    
    fields = get_inventory_fields()
    field_names = [field["name"] for field in fields]
    
    # Calculate pagination
    total_items = len(items)
    start_idx = current_page * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)
    
    # Show only current page items
    page_items = items[start_idx:end_idx]
    
    # Batch insert for better performance
    for i, item in enumerate(page_items, start_idx + 1):
        values = [str(i)]  # Global index column
        
        # Add ALL field values using cached field names
        for field_name in field_names:
            value = item.data.get(field_name, "")
            values.append(str(value) if value is not None else "")
        
        table.insert('', 'end', values=values)
    
    # Update window title with pagination info
    if hasattr(table.master, 'winfo_toplevel'):
        toplevel = table.winfo_toplevel()
        if total_items > items_per_page:
            page_info = f" - Page {current_page + 1}/{(total_items - 1) // items_per_page + 1} ({start_idx + 1}-{end_idx} of {total_items})"
            if hasattr(toplevel, 'title'):
                current_title = toplevel.title()
                if " - Page " in current_title:
                    base_title = current_title.split(" - Page ")[0]
                else:
                    base_title = current_title
                toplevel.title(base_title + page_info)


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

    # Define colors - Modern light theme
    BG_COLOR = "#F0F0F0"        # Light gray background
    FG_COLOR = "#2C3E50"        # Dark blue-gray text
    PRIMARY_COLOR = "#3498DB"   # Blue accent
    SECONDARY_COLOR = "#2ECC71" # Green accent
    ENTRY_BG = "#FFFFFF"        # White input fields
    BUTTON_COLOR = "#34495E"    # Dark gray buttons
    BUTTON_HOVER = "#2C3E50"    # Darker on hover

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
        borderwidth=1,
        relief="solid",
        padding=(8, 6),
        font=entry_font,
    )
    style.map("TEntry", 
              fieldbackground=[("focus", "#FFFFFF")],
              bordercolor=[("focus", PRIMARY_COLOR)])
    style.configure(
        "TButton",
        background=BUTTON_COLOR,
        foreground="#FFFFFF",
        borderwidth=1,
        relief="flat",
        padding=(12, 8),
        font=("Segoe UI", 10, "bold"),
    )
    style.map(
        "TButton",
        background=[("active", BUTTON_HOVER), ("!disabled", BUTTON_COLOR)],
        foreground=[("active", "#FFFFFF")],
        relief=[("pressed", "sunken"), ("!pressed", "flat")],
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
    
    # Configure Treeview for table display
    style.configure(
        "Treeview",
        background="#FFFFFF",  # White background for data visibility
        foreground="#000000",  # Black text for contrast
        fieldbackground="#FFFFFF",
        borderwidth=1,
        relief="solid",
        font=("Segoe UI", 10),
        rowheight=25
    )
    style.configure(
        "Treeview.Heading",
        background="#E1E1E1",  # Light gray headers
        foreground="#000000",
        borderwidth=1,
        relief="raised",
        font=("Segoe UI", 10, "bold"),
        padding=(5, 5)
    )
    style.map(
        "Treeview",
        background=[("selected", "#4A90E2")],
        foreground=[("selected", "#FFFFFF")]
    )
    style.map(
        "Treeview.Heading",
        background=[("active", "#D0D0D0")]
    )


# --- Core Application Logic ---


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
                if field["type"] == "INTEGER":
                    value = int(value)
                elif field["type"] == "REAL":
                    value = Decimal(value)
            except ValueError:
                messagebox.showerror("Error", f"Invalid value for '{field_name}'. Expected {field['type']}.")
                return
        
        item_data[field_name] = value
    
    try:
        item = Item(**item_data)
        inventory.add_item(item)
        mark_for_save()
        save_inventory_to_database()
        # Update filtered_items with all current items and refresh
        global filtered_items, current_page
        filtered_items = inventory.get_all_items()
        current_page = 0  # Reset to first page to show new item
        refresh_listbox(listbox, filtered_items)
        clear_entries()
        messagebox.showinfo("Success", "Item added successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to add item: {str(e)}")


def update_item(listbox):
    """Update the currently selected item in the inventory."""
    global inventory, field_entries
    
    if not field_entries:
        messagebox.showerror("Error", "No input fields available.")
        return
    
    # Get selected item from treeview
    selected_items = listbox.selection()
    if not selected_items:
        messagebox.showerror("Error", "Please select an item to update.")
        return
    
    # Get the item index from the first column of the selected row
    item_values = listbox.item(selected_items[0])['values']
    if not item_values:
        messagebox.showerror("Error", "Invalid selection.")
        return
    
    # The first column contains the item index (1-based)
    try:
        item_index = int(item_values[0]) - 1
        items = inventory.get_all_items()
        if item_index >= len(items):
            messagebox.showerror("Error", "Invalid item selection.")
            return
        selected_item = items[item_index]
    except (ValueError, IndexError):
        messagebox.showerror("Error", "Invalid item selection.")
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
                if field["type"] == "INTEGER":
                    value = int(value)
                elif field["type"] == "REAL":
                    value = Decimal(value)
            except ValueError:
                messagebox.showerror("Error", f"Invalid value for '{field_name}'. Expected {field['type']}.")
                return
        
        item_data[field_name] = value
    
    try:
        # Update the item's data
        for field_name, value in item_data.items():
            selected_item.update_field(field_name, value)
        
        mark_for_save()
        save_inventory_to_database()
        # Update filtered_items with all current items and refresh
        global filtered_items
        filtered_items = inventory.get_all_items()
        refresh_listbox(listbox, filtered_items)
        clear_entries()
        messagebox.showinfo("Success", "Item updated successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to update item: {str(e)}")


def delete_item(listbox):
    """Delete the selected item from the inventory."""
    global inventory
    
    selected_items = listbox.selection()
    if not selected_items:
        messagebox.showerror("Error", "Please select an item to delete.")
        return
    
    # Confirm deletion
    result = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this item?")
    if not result:
        return
    
    try:
        # Get the item index from the first column of the selected row
        item_values = listbox.item(selected_items[0])['values']
        if not item_values:
            messagebox.showerror("Error", "Invalid selection.")
            return
        
        # The first column contains the item index (1-based)
        item_index = int(item_values[0]) - 1
        items = inventory.get_all_items()
        if item_index >= len(items):
            messagebox.showerror("Error", "Invalid item selection.")
            return
        
        selected_item = items[item_index]
        inventory.remove_item(selected_item.id)
        mark_for_save()
        save_inventory_to_database()
        # Update filtered_items with all current items and refresh
        global filtered_items
        filtered_items = inventory.get_all_items()
        refresh_listbox(listbox, filtered_items)
        clear_entries()
        messagebox.showinfo("Success", "Item deleted successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to delete item: {str(e)}")


def clear_entries():
    """Clear all field entries."""
    global field_entries
    
    for entry_widget in field_entries.values():
        if hasattr(entry_widget, 'delete'):
            entry_widget.delete(0, tk.END)


def on_item_select(event, listbox):
    """Populate the entry fields with data from the selected treeview item."""
    global inventory, field_entries
    
    selected_items = listbox.selection()
    if not selected_items:
        return
    
    try:
        # Get the item index from the first column of the selected row
        item_values = listbox.item(selected_items[0])['values']
        if not item_values:
            return
        
        # The first column contains the item index (1-based)
        item_index = int(item_values[0]) - 1
        items = inventory.get_all_items()
        if item_index >= len(items):
            return
        
        selected_item = items[item_index]
        
        # Clear all fields first
        clear_entries()
        
        # Populate fields with item data
        for field_name, entry_widget in field_entries.items():
            if hasattr(entry_widget, 'insert'):
                value = selected_item.data.get(field_name, "")
                entry_widget.insert(0, str(value))
                
    except (IndexError, KeyError, ValueError):
        pass  # Ignore selection errors

def search_items(search_entry, listbox):
    """Search for items based on the search query."""
    global inventory, current_page
    
    query = search_entry.get().strip()
    current_page = 0  # Reset to first page when searching
    
    if not query:
        # If no query, show all items
        refresh_listbox(listbox, filtered_items)
        return
    
    # Search for matching items
    matching_items = inventory.search_items(query)
    
    # Use the optimized refresh function with filtered items
    refresh_listbox(listbox, matching_items)

def next_page(listbox):
    """Go to next page."""
    global current_page, filtered_items, items_per_page
    
    total_pages = (len(filtered_items) - 1) // items_per_page + 1
    if current_page < total_pages - 1:
        current_page += 1
        refresh_listbox(listbox, filtered_items)

def prev_page(listbox):
    """Go to previous page."""
    global current_page, filtered_items
    
    if current_page > 0:
        current_page -= 1
        refresh_listbox(listbox, filtered_items)

def set_items_per_page(new_size, listbox):
    """Change the number of items displayed per page."""
    global items_per_page, current_page
    
    items_per_page = new_size
    current_page = 0  # Reset to first page
    refresh_listbox(listbox, filtered_items)





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

def import_datasheet(listbox):
    """Import data from CSV/TXT files."""
    global inventory, database
    
    # Get supported file types for dialog
    extensions = get_supported_extensions()
    filetypes = []
    filetypes.append(("CSV files", "*.csv"))
    filetypes.append(("Text files", "*.txt"))
    filetypes.append(("All supported", "*.csv;*.txt"))
    filetypes.append(("All files", "*.*"))
    
    file_path = filedialog.askopenfilename(
        title="Import Datasheet",
        filetypes=filetypes
    )
    
    if not file_path:
        return
    
    try:
        # Ask user if they want to change inventory type for this import
        result = messagebox.askyesno("Import Options", 
            "Do you want to change the inventory type for this import?\n\n"
            f"Current type: {get_inventory_type().title()}")
        
        if result:
            change_inventory_type()
        
        # Import the file
        tables = ingest_file(file_path)
        
        if not tables:
            messagebox.showwarning("Import", "No data found in the selected file.")
            return
        
        imported_count = 0
        for table_name, data in tables:
            columns = data['columns']
            rows = data['rows']
            
            # Try to map columns to current inventory fields
            current_fields = get_inventory_fields()
            field_mapping = {}
            
            # Simple mapping - look for similar names
            for col in columns:
                for field in current_fields:
                    if col.lower() in field['name'].lower() or field['name'].lower() in col.lower():
                        field_mapping[col] = field['name']
                        break
            
            # Import rows
            for row in rows:
                if len(row) != len(columns):
                    continue  # Skip malformed rows
                
                item_data = {}
                for i, col in enumerate(columns):
                    if i < len(row):
                        value = row[i].strip() if row[i] else ""
                        if col in field_mapping:
                            # Map to inventory field
                            field_name = field_mapping[col]
                            # Find field config for type conversion
                            field_config = next((f for f in current_fields if f['name'] == field_name), None)
                            if field_config and value:
                                try:
                                    if field_config['type'] == 'INTEGER':
                                        value = int(float(value))  # Handle decimal strings
                                    elif field_config['type'] == 'REAL':
                                        value = float(value)
                                except ValueError:
                                    pass  # Keep as string if conversion fails
                            item_data[field_name] = value
                
                # Only create item if we have at least the required fields
                required_fields = [f['name'] for f in current_fields if f['required']]
                if all(field in item_data and item_data[field] for field in required_fields):
                    try:
                        item = Item(**item_data)
                        inventory.add_item(item)
                        imported_count += 1
                    except Exception as e:
                        print(f"Error creating item: {e}")
        
        # Save to database and refresh
        if imported_count > 0:
            save_inventory_to_database()
            # Reset to show all items after import
            global filtered_items, current_page
            current_page = 0
            filtered_items = inventory.get_all_items()
            refresh_listbox(listbox, filtered_items)
            messagebox.showinfo("Import Complete", 
                f"Successfully imported {imported_count} items.")
        else:
            messagebox.showwarning("Import", 
                "No items could be imported. Check that your file has the required fields.")
    
    except Exception as e:
        messagebox.showerror("Import Error", f"Error importing file: {str(e)}")

def view_database_tables():
    """Show database tables and their structure."""
    global database
    
    if not database:
        messagebox.showwarning("Database", "No database is currently loaded.")
        return
    
    try:
        # Create a new window to show database info
        db_window = tk.Toplevel()
        db_window.title("Database Structure")
        db_window.geometry("800x600")
        db_window.configure(bg="#F0F0F0")
        
        # Create notebook for tabs
        notebook = ttk.Notebook(db_window)
        notebook.pack(expand=True, fill='both', padx=10, pady=10)
        
        # Tab 1: Tables Overview
        tables_frame = ttk.Frame(notebook)
        notebook.add(tables_frame, text="Tables")
        
        # Get tables from database
        cursor = database.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        ttk.Label(tables_frame, text="Database Tables", font=("Segoe UI", 14, "bold")).pack(pady=10)
        
        # Create treeview for tables
        tables_tree = ttk.Treeview(tables_frame, columns=('Table Name', 'Type'), show='headings', height=10)
        tables_tree.heading('#1', text='Table Name')
        tables_tree.heading('#2', text='Type')
        tables_tree.column('#1', width=200)
        tables_tree.column('#2', width=100)
        
        for table in tables:
            tables_tree.insert('', 'end', values=(table[0], 'Table'))
        
        tables_tree.pack(expand=True, fill='both', padx=10, pady=10)
        
        # Tab 2: Current Table Structure
        structure_frame = ttk.Frame(notebook)
        notebook.add(structure_frame, text="Current Table Schema")
        
        ttk.Label(structure_frame, text="Current Inventory Table Schema", font=("Segoe UI", 14, "bold")).pack(pady=10)
        
        # Get current table structure
        cursor.execute("PRAGMA table_info(inventory_items);")
        columns = cursor.fetchall()
        
        # Create treeview for column info
        cols_tree = ttk.Treeview(structure_frame, columns=('Column', 'Type', 'Required', 'Key'), show='headings', height=15)
        cols_tree.heading('#1', text='Column Name')
        cols_tree.heading('#2', text='Data Type')
        cols_tree.heading('#3', text='Required')
        cols_tree.heading('#4', text='Primary Key')
        
        for col in columns:
            cols_tree.insert('', 'end', values=(
                col[1],  # name
                col[2],  # type
                'Yes' if col[3] else 'No',  # not null
                'Yes' if col[5] else 'No'   # primary key
            ))
        
        cols_tree.pack(expand=True, fill='both', padx=10, pady=10)
        
        # Tab 3: Data Sample
        data_frame = ttk.Frame(notebook)
        notebook.add(data_frame, text="Sample Data")
        
        ttk.Label(data_frame, text="Sample Records", font=("Segoe UI", 14, "bold")).pack(pady=10)
        
        # Get sample data
        cursor.execute("SELECT * FROM inventory_items LIMIT 5;")
        sample_data = cursor.fetchall()
        
        if sample_data:
            # Get column names
            cursor.execute("PRAGMA table_info(inventory_items);")
            column_info = cursor.fetchall()
            column_names = [col[1] for col in column_info]
            
            # Create treeview for sample data
            data_tree = ttk.Treeview(data_frame, columns=column_names, show='headings', height=8)
            
            for col in column_names:
                data_tree.heading(col, text=col)
                data_tree.column(col, width=100)
            
            for row in sample_data:
                data_tree.insert('', 'end', values=row)
            
            data_tree.pack(expand=True, fill='both', padx=10, pady=10)
            
            # Add scrollbars
            v_scroll = ttk.Scrollbar(data_frame, orient="vertical", command=data_tree.yview)
            v_scroll.pack(side="right", fill="y")
            data_tree.config(yscrollcommand=v_scroll.set)
            
            h_scroll = ttk.Scrollbar(data_frame, orient="horizontal", command=data_tree.xview)
            h_scroll.pack(side="bottom", fill="x")
            data_tree.config(xscrollcommand=h_scroll.set)
        else:
            ttk.Label(data_frame, text="No sample data available").pack(pady=20)
        
        # Add close button
        ttk.Button(db_window, text="Close", command=db_window.destroy).pack(pady=10)
        
    except Exception as e:
        messagebox.showerror("Database Error", f"Error viewing database structure: {str(e)}")

def refresh_ui_after_type_change(new_type):
    """Refresh both the table and input fields after inventory type change."""
    global field_entries, listbox, input_frame
    
    print(f"Refreshing UI for inventory type change to: {new_type.value}")
    
    try:
        # Recreate input fields based on new type  
        if 'input_frame' in globals() and input_frame:
            print("Updating input fields...")
            create_input_fields(input_frame)
        
        # Recreate table columns based on new type
        if 'listbox' in globals() and listbox:
            print("Updating table columns...")
            # Get new fields configuration
            fields = get_inventory_fields()
            print(f"New fields: {[f['name'] for f in fields]}")
            
            # Clear existing items first
            for item in listbox.get_children():
                listbox.delete(item)
            
            # Reconfigure table columns
            new_columns = ['#'] + [field['name'].title() for field in fields]
            listbox['columns'] = new_columns
            
            # Reconfigure column headings and widths
            listbox.heading('#1', text='#')
            listbox.column('#1', width=40, anchor='center')
            
            for i, field in enumerate(fields, 1):
                col_name = field['name'].replace('_', ' ').title()
                listbox.heading(f'#{i+1}', text=col_name)
                width = max(100, len(col_name) * 10 + 20)
                listbox.column(f'#{i+1}', width=width, anchor='w')
            
            print("Reloading data from database with new schema...")
            # Reload data from database with new field schema
            load_inventory_from_database()
            
            # Refresh table data
            print("Refreshing table display...")
            refresh_listbox(listbox, filtered_items)
            
            # Force UI update
            listbox.update_idletasks()
            
        print("UI refresh complete!")
        
    except Exception as e:
        print(f"Error during UI refresh: {e}")
        messagebox.showerror("UI Error", f"Error refreshing interface: {str(e)}")

def change_inventory_type():
    """Allow user to change inventory type."""
    global field_entries
    
    # Create dialog for inventory type selection
    dialog = tk.Toplevel()
    dialog.title("Change Inventory Type")
    dialog.geometry("400x300")
    dialog.grab_set()  # Make it modal
    
    ttk.Label(dialog, text="Select Inventory Type:", font=("Segoe UI", 12, "bold")).pack(pady=10)
    
    # Get available types
    types = get_inventory_types()
    selected_type = tk.StringVar(value=get_inventory_type())
    
    for inv_type in types:
        ttk.Radiobutton(
            dialog, 
            text=f"{inv_type['name']} - {inv_type['description']}", 
            variable=selected_type, 
            value=inv_type['id']
        ).pack(anchor="w", padx=20, pady=5)
    
    def apply_change():
        new_type_str = selected_type.get()
        for inv_type in InventoryType:
            if inv_type.value == new_type_str:
                set_inventory_type(inv_type)
                from core.config import save_config
                save_config(inv_type)
                
                # Dynamically recreate input fields and refresh display
                refresh_ui_after_type_change(inv_type)
                messagebox.showinfo("Type Changed", 
                    f"Inventory type changed to {inv_type.value.title()}.\n"
                    "Form fields and table have been updated!")
                break
        dialog.destroy()
    
    ttk.Button(dialog, text="Apply", command=apply_change).pack(pady=10)
    ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack()

def clear_all_data(listbox):
    """Clear all inventory data."""
    global inventory, database
    
    result = messagebox.askyesno("Clear All Data", 
        "Are you sure you want to delete ALL inventory data?\n\n"
        "This action cannot be undone!")
    
    if result:
        # Confirm again
        result2 = messagebox.askyesno("Final Confirmation", 
            "This will permanently delete all your inventory data.\n\n"
            "Are you absolutely sure?")
        
        if result2:
            try:
                # Clear database
                if database:
                    database.clear_items()
                
                # Clear in-memory inventory
                inventory = Inventory()
                
                # Refresh GUI
                refresh_listbox(listbox, filtered_items)
                clear_entries()
                
                messagebox.showinfo("Data Cleared", "All inventory data has been deleted.")
            except Exception as e:
                messagebox.showerror("Error", f"Error clearing data: {str(e)}")

def reset_to_default(listbox):
    """Reset system to initial state."""
    global inventory, database
    
    result = messagebox.askyesno("Reset System", 
        "Reset the system to initial state?\n\n"
        "This will:\n"
        "- Clear all inventory data\n" 
        "- Reset inventory type to Warehouse\n"
        "- Clear all settings")
    
    if result:
        try:
            # Clear database
            if database:
                database.clear_items()
            
            # Reset inventory type
            set_inventory_type(InventoryType.WAREHOUSE)
            from core.config import save_config
            save_config(InventoryType.WAREHOUSE)
            
            # Clear in-memory inventory
            inventory = Inventory()
            
            # Refresh GUI
            refresh_listbox(listbox, filtered_items)
            clear_entries()
            
            messagebox.showinfo("System Reset", 
                "System has been reset to initial state.\n"
                "Inventory type: Warehouse\n"
                "Please restart the application to see updated fields.")
        except Exception as e:
            messagebox.showerror("Error", f"Error resetting system: {str(e)}")

def run_gui():
    """Initialize and run the flexible inventory GUI."""
    global field_entries, database, input_frame, listbox
    
    # Initialize inventory setup
    initialize_inventory_setup()
    
    # Initialize database
    database = Database()
    load_inventory_from_database()
    
    root = tk.Tk()
    root.title("Inventory Management System")
    root.geometry("1200x800")
    root.configure(bg="#F0F0F0")  # Light gray background
    root.minsize(1000, 600)  # Minimum window size
    
    setup_styles()
    
    # Create menu bar with better styling
    menubar = tk.Menu(root, bg="#E1E1E1", fg="#000000", activebackground="#4A90E2", activeforeground="#FFFFFF")
    root.config(menu=menubar)
    
    # File menu
    file_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Import Datasheet...", command=lambda: import_datasheet(listbox))
    file_menu.add_separator()
    file_menu.add_command(label="Choose Database...", command=lambda: choose_database(root, listbox))
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=root.quit)
    
    # Tools menu
    tools_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Tools", menu=tools_menu)
    tools_menu.add_command(label="Change Inventory Type...", command=change_inventory_type)
    tools_menu.add_separator()
    tools_menu.add_command(label="View Database Tables...", command=view_database_tables)
    tools_menu.add_separator()
    tools_menu.add_command(label="Clear All Data...", command=lambda: clear_all_data(listbox))
    tools_menu.add_command(label="Reset to Default...", command=lambda: reset_to_default(listbox))
    
    # Main container
    main_frame = ttk.Frame(root, padding="10")
    main_frame.pack(expand=True, fill="both")
    
    # Create a placeholder listbox variable that we'll update later
    listbox = None
    
    # Top frame with database and inventory type info
    top_frame = ttk.Frame(main_frame)
    top_frame.pack(fill="x", pady=(0, 10))
    
    inventory_type = get_inventory_type()
    ttk.Label(top_frame, text=f"Inventory Type: {inventory_type.title()}").pack(side="left")
    
    # Toolbar buttons
    toolbar_frame = ttk.Frame(top_frame)
    toolbar_frame.pack(side="right")
    
    # Main content area (create listbox first)
    content_frame = ttk.Frame(main_frame)
    content_frame.pack(expand=True, fill="both", pady=(10, 0))
    
    # Left side - Item list
    left_frame = ttk.Frame(content_frame)
    left_frame.pack(side="left", expand=True, fill="both", padx=(0, 10))
    
    ttk.Label(left_frame, text="Inventory Data").pack(anchor="w", pady=(0, 5))
    
    # Create table frame
    table_frame = ttk.Frame(left_frame)
    table_frame.pack(expand=True, fill="both")
    
    # Create Treeview for table display
    fields = get_inventory_fields()
    columns = ['#'] + [field['name'].title() for field in fields]  # Show ALL fields + index
    
    listbox = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
    
    # Configure column headings and widths
    listbox.heading('#1', text='#')
    listbox.column('#1', width=40, anchor='center')
    
    # Configure ALL field columns dynamically
    for i, field in enumerate(fields, 1):
        col_name = field['name'].replace('_', ' ').title()
        listbox.heading(f'#{i+1}', text=col_name)
        # Adjust width based on field type and name length
        width = max(100, len(col_name) * 10 + 20)
        listbox.column(f'#{i+1}', width=width, anchor='w')
    
    listbox.pack(side="left", expand=True, fill="both")
    
    # Add pagination controls
    pagination_frame = ttk.Frame(left_frame)
    pagination_frame.pack(fill="x", pady=(5, 0))
    
    ttk.Button(pagination_frame, text="◀ Prev", 
               command=lambda: prev_page(listbox)).pack(side="left", padx=(0, 5))
    
    ttk.Button(pagination_frame, text="Next ▶", 
               command=lambda: next_page(listbox)).pack(side="left", padx=(0, 10))
    
    # Items per page selector
    ttk.Label(pagination_frame, text="Items per page:").pack(side="left", padx=(0, 5))
    page_size_var = tk.StringVar(value="100")
    page_size_combo = ttk.Combobox(pagination_frame, textvariable=page_size_var, 
                                   values=["50", "100", "200", "500", "1000"], 
                                   width=8, state="readonly")
    page_size_combo.pack(side="left", padx=(0, 10))
    page_size_combo.bind('<<ComboboxSelected>>', 
                         lambda e: set_items_per_page(int(page_size_var.get()), listbox))
    
    # Scrollbars for table
    v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=listbox.yview)
    v_scrollbar.pack(side="right", fill="y")
    listbox.config(yscrollcommand=v_scrollbar.set)
    
    h_scrollbar = ttk.Scrollbar(left_frame, orient="horizontal", command=listbox.xview)
    h_scrollbar.pack(side="bottom", fill="x")
    listbox.config(xscrollcommand=h_scrollbar.set)
    
    # Now that listbox is created, connect the toolbar buttons
    ttk.Button(
        toolbar_frame,
        text="Import Data",
        command=lambda: import_datasheet(listbox)
    ).pack(side="left", padx=(0, 5))
    
    ttk.Button(
        toolbar_frame,
        text="Change Type",
        command=change_inventory_type
    ).pack(side="left", padx=(0, 5))
    
    ttk.Button(
        toolbar_frame,
        text="Database",
        command=lambda: choose_database(root, listbox)
    ).pack(side="left")
    
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
    
    # Separator
    ttk.Separator(buttons_frame, orient="horizontal").pack(fill="x", pady=10)
    
    # Data management buttons
    ttk.Label(buttons_frame, text="Data Management", font=("Segoe UI", 9, "bold")).pack(anchor="w")
    
    ttk.Button(
        buttons_frame,
        text="Clear All Data",
        command=lambda: clear_all_data(listbox)
    ).pack(fill="x", pady=2)
    
    ttk.Button(
        buttons_frame,
        text="Reset System",
        command=lambda: reset_to_default(listbox)
    ).pack(fill="x", pady=2)
    
    # Bind item selection event
    listbox.bind(
        "<<TreeviewSelect>>",
        lambda event: on_item_select(event, listbox)
    )
    
    # Load initial data - start with all items
    refresh_listbox(listbox)
    
    root.mainloop()


if __name__ == "__main__":
    run_gui()

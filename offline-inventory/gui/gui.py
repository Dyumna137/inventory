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
            refresh_listbox(listbox)
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
            print(f"Loaded item: {item.data.get('name', 'Unknown')} (ID: {item.id})")
        except Exception as e:
            print(f"Error loading item: {e}")
            print(f"Item data was: {item_data}")
            print(f"Item data: {item_data}")
    
    print(f"Successfully loaded {len(inventory.get_all_items())} items into inventory")

def save_inventory_to_database():
    """Save all inventory items to the database."""
    global inventory, database
    
    if not database:
        return
    
    # Clear existing items and save current inventory
    database.clear_items()
    
    for item in inventory.get_all_items():
        database.save_item(item.to_dict())


def refresh_listbox(table):
    """Refresh the table with current inventory items."""
    global inventory
    
    print(f"Refreshing table - inventory exists: {inventory is not None}")
    
    # Clear existing items
    for item in table.get_children():
        table.delete(item)
    
    if not inventory:
        print("No inventory object found")
        return
    
    items = inventory.get_all_items()
    print(f"Found {len(items)} items in inventory")
    
    fields = get_inventory_fields()
    print(f"Using fields: {[f['name'] for f in fields]}")
    
    # Add items to table
    for i, item in enumerate(items, 1):
        values = [str(i)]  # Index column
        
        # Add ALL field values
        for field in fields:  # Show ALL fields
            field_name = field["name"]
            value = item.data.get(field_name, "")
            if value is None:
                value = ""
            values.append(str(value))
        
        table.insert('', 'end', values=values)
        print(f"Added to table [{i}]: {item.data.get('name', 'Unknown')}")
    
    print(f"Table now has {len(items)} items")


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
        save_inventory_to_database()
        refresh_listbox(listbox)
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
    
    # Get selected item from listbox
    selected_index = listbox.curselection()
    if not selected_index:
        messagebox.showerror("Error", "Please select an item to update.")
        return
    
    selected_item_id = list(inventory.items.keys())[selected_index[0]]
    selected_item = inventory.get_item(selected_item_id)
    
    if not selected_item:
        messagebox.showerror("Error", "Selected item not found.")
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
        
        save_inventory_to_database()
        refresh_listbox(listbox)
        clear_entries()
        messagebox.showinfo("Success", "Item updated successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to update item: {str(e)}")


def delete_item(listbox):
    """Delete the selected item from the inventory."""
    global inventory
    
    selected_index = listbox.curselection()
    if not selected_index:
        messagebox.showerror("Error", "Please select an item to delete.")
        return
    
    # Confirm deletion
    result = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this item?")
    if not result:
        return
    
    try:
        selected_item_id = list(inventory.items.keys())[selected_index[0]]
        inventory.remove_item(selected_item_id)
        save_inventory_to_database()
        refresh_listbox(listbox)
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
    """Populate the entry fields with data from the selected listbox item."""
    global inventory, field_entries
    
    selected_index = listbox.curselection()
    if not selected_index:
        return
    
    try:
        selected_item_id = list(inventory.items.keys())[selected_index[0]]
        selected_item = inventory.get_item(selected_item_id)
        
        if not selected_item:
            return
        
        # Clear all fields first
        clear_entries()
        
        # Populate fields with item data
        for field_name, entry_widget in field_entries.items():
            if hasattr(entry_widget, 'insert'):
                value = selected_item.data.get(field_name, "")
                entry_widget.insert(0, str(value))
                
    except (IndexError, KeyError):
        pass  # Ignore selection errors

def search_items(search_entry, listbox):
    """Search for items based on the search query."""
    global inventory
    
    query = search_entry.get().strip()
    
    # Clear the listbox
    listbox.delete(0, tk.END)
    
    if not query:
        # If no query, show all items
        refresh_listbox(listbox)
        return
    
    # Search for matching items
    matching_items = inventory.search_items(query)
    fields = get_inventory_fields()
    
    for item in matching_items:
        # Create display string based on configured fields
        display_parts = []
        for field in fields[:3]:  # Show first 3 fields in list
            field_name = field["name"]
            value = item.data.get(field_name, "")
            display_parts.append(f"{field_name.title()}: {value}")
        
        listbox.insert(tk.END, " | ".join(display_parts))





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

def on_item_select(event, table):
    """Populate input fields when an item is selected."""
    global inventory, field_entries
    
    selection = table.selection()
    if not selection:
        return
    
    # Get the selected item index from the first column (index)
    item = table.item(selection[0])
    values = item['values']
    if not values:
        return
    
    # The first value is the index (1-based), convert to 0-based for list access
    try:
        item_index = int(values[0]) - 1
        items = inventory.get_all_items()
        if item_index >= len(items):
            return
        
        selected_item = items[item_index]
        
        # Clear and populate fields
        clear_entries()
        
        for field_name, entry_widget in field_entries.items():
            value = selected_item.data.get(field_name, "")
            if value is not None:
                entry_widget.insert(0, str(value))
    except (ValueError, IndexError) as e:
        print(f"Error selecting item: {e}")

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
            refresh_listbox(listbox)
            messagebox.showinfo("Import Complete", 
                f"Successfully imported {imported_count} items.")
        else:
            messagebox.showwarning("Import", 
                "No items could be imported. Check that your file has the required fields.")
    
    except Exception as e:
        messagebox.showerror("Import Error", f"Error importing file: {str(e)}")

def refresh_ui_after_type_change(new_type):
    """Refresh both the table and input fields after inventory type change."""
    global field_entries, listbox, input_frame
    
    # Recreate input fields based on new type
    if 'input_frame' in globals() and input_frame:
        create_input_fields(input_frame)
    
    # Recreate table columns based on new type
    if 'listbox' in globals() and listbox:
        # Get new fields configuration
        fields = get_inventory_fields()
        
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
        
        # Refresh table data
        refresh_listbox(listbox)

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
                refresh_listbox(listbox)
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
            refresh_listbox(listbox)
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
    
    # Load initial data
    refresh_listbox(listbox)
    
    root.mainloop()


if __name__ == "__main__":
    run_gui()

# gui.py (Tkinter for now)
import tkinter as tk
from tkinter import messagebox, ttk, font, filedialog
from db import database
from core import datasheet_importer
from db.database import save_dataframe

# Store the database items in a local list
items = []

# --- Modern UI Enhancements ---
def setup_styles():
    """Sets up modern styling for the application."""
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
    
    # Configure styles
    style.configure(".", background=BG_COLOR, foreground=FG_COLOR, font=default_font)
    style.configure("TFrame", background=BG_COLOR)
    style.configure("TLabel", background=BG_COLOR, foreground=FG_COLOR, padding=(5, 5))
    style.configure("TEntry", 
                    fieldbackground=ENTRY_BG, 
                    foreground=FG_COLOR, 
                    insertcolor=FG_COLOR,
                    borderwidth=0,
                    font=entry_font)
    style.map("TEntry",
              fieldbackground=[("focus", "#444444")])

    style.configure("TButton", 
                    background=BUTTON_COLOR, 
                    foreground=FG_COLOR,
                    borderwidth=1,
                    padding=(10, 5),
                    font=("Segoe UI", 10, "bold"))
    style.map("TButton",
              background=[("active", BUTTON_HOVER), ("!disabled", BUTTON_COLOR)],
              foreground=[("active", FG_COLOR)])

    style.configure("TListbox", 
                    background=ENTRY_BG, 
                    foreground=FG_COLOR,
                    selectbackground=PRIMARY_COLOR,
                    selectforeground=FG_COLOR,
                    borderwidth=0,
                    highlightthickness=0)

# --- Core Application Logic ---
def refresh_listbox(listbox):
    """Refreshes the listbox with the latest items from the database."""
    global items
    listbox.delete(0, tk.END)
    items = database.fetch_items()
    for item in items:
        listbox.insert(tk.END, f"{item[1]} (x{item[2]}) - ${item[3]:.2f}")

def add_item(name_entry, quantity_entry, price_entry, listbox):
    """Adds a new item to the database."""
    name = name_entry.get()
    quantity = quantity_entry.get()
    price = price_entry.get()

    if not name or not quantity or not price:
        messagebox.showerror("Error", "All fields are required.")
        return

    try:
        database.insert_item(name, int(quantity), float(price))
        refresh_listbox(listbox)
        clear_entries(name_entry, quantity_entry, price_entry)
    except ValueError:
        messagebox.showerror("Error", "Invalid input: Quantity must be an integer and Price must be a number.")

def update_item(name_entry, quantity_entry, price_entry, listbox):
    """Updates an existing item in the database."""
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
        database.update_item(selected_item_id, name, int(quantity), float(price))
        refresh_listbox(listbox)
        clear_entries(name_entry, quantity_entry, price_entry)
    except ValueError:
        messagebox.showerror("Error", "Invalid input: Quantity must be an integer and Price must be a number.")

def delete_item(listbox):
    """Deletes a selected item from the database."""
    selected_item_index = listbox.curselection()
    if not selected_item_index:
        messagebox.showerror("Error", "Please select an item to delete.")
        return

    selected_item_id = items[selected_item_index[0]][0]
    database.delete_item(selected_item_id)
    refresh_listbox(listbox)

def clear_entries(*entries):
    """Clears all given entry widgets."""
    for entry in entries:
        entry.delete(0, tk.END)

def on_item_select(event, name_entry, quantity_entry, price_entry):
    """Populates entry fields when an item is selected from the listbox."""
    selected_item_index = event.widget.curselection()
    if not selected_item_index:
        return

    selected_item = items[selected_item_index[0]]
    clear_entries(name_entry, quantity_entry, price_entry)
    name_entry.insert(0, selected_item[1])
    quantity_entry.insert(0, selected_item[2])
    price_entry.insert(0, f"{selected_item[3]:.2f}")


def import_datasheet():
    file_path = filedialog.askopenfilename(
        title="Select Datasheet",
        filetypes=[("Supported files", "*.csv *.xls *.xlsx *.pdf *.txt *.png *.jpg *.jpeg")]
    )
    if not file_path:
        return

    try:
        tables = datasheet_importer.ingest_file(file_path)
        for name, df in tables:
            save_dataframe(df, datasheet_importer.slugify(name))
        messagebox.showinfo("Success", f"Imported {len(tables)} table(s) from {file_path}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# --- GUI Setup ---
def run_gui():
    """Initializes and runs the main GUI."""
    root = tk.Tk()
    root.title("Offline Inventory Management")
    root.geometry("600x500")
    root.configure(bg="#2E2E2E")

    setup_styles()

    main_frame = ttk.Frame(root, padding="10")
    main_frame.pack(expand=True, fill="both")

    # --- Input Frame ---
    input_frame = ttk.Frame(main_frame)
    input_frame.pack(fill="x", pady=(0, 10))
    input_frame.columnconfigure(1, weight=1)

    ttk.Label(input_frame, text="Name:").grid(row=0, column=0, sticky="w", padx=(0, 5))
    name_entry = ttk.Entry(input_frame)
    name_entry.grid(row=0, column=1, sticky="ew")

    ttk.Label(input_frame, text="Quantity:").grid(row=1, column=0, sticky="w", padx=(0, 5))
    quantity_entry = ttk.Entry(input_frame)
    quantity_entry.grid(row=1, column=1, sticky="ew")

    ttk.Label(input_frame, text="Price:").grid(row=2, column=0, sticky="w", padx=(0, 5))
    price_entry = ttk.Entry(input_frame)
    price_entry.grid(row=2, column=1, sticky="ew")
    
    for widget in input_frame.winfo_children():
        widget.grid_configure(pady=5)

    # --- Button Frame ---
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill="x", pady=10)
    button_frame.columnconfigure((0, 1, 2, 3, 4), weight=1)

    #--- Button for Add Item ---
    ttk.Button(
        button_frame, text="Add Item",
        command=lambda: add_item(name_entry, quantity_entry, price_entry, listbox)
    ).grid(row=0, column=0, sticky="ew", padx=5)

    #--- Button for Update Item ---
    ttk.Button(
        button_frame, text="Update Item",
        command=lambda: update_item(name_entry, quantity_entry, price_entry, listbox)
    ).grid(row=0, column=1, sticky="ew", padx=5)

    #--- Button for Delete Item ---
    ttk.Button(
        button_frame, text="Delete Item",
        command=lambda: delete_item(listbox)
    ).grid(row=0, column=2, sticky="ew", padx=5)
    
    #--- Button for Clear Entries ---
    ttk.Button(
        button_frame, text="Clear Entries",
        command=lambda: clear_entries(name_entry, quantity_entry, price_entry)
    ).grid(row=0, column=3, sticky="ew", padx=5)

    #--- Button for Import Datasheet ---
    ttk.Button(
        button_frame, text="Import Datasheet",
        command=import_datasheet
    ).grid(row=0, column=4, sticky="ew", padx=5)

    # --- Listbox ---
    listbox_frame = ttk.Frame(main_frame)
    listbox_frame.pack(expand=True, fill="both")
    
    listbox = tk.Listbox(listbox_frame, 
                         width=60, 
                         height=15,
                         background="#3A3A3A",
                         foreground="#FFFFFF",
                         selectbackground="#4A90E2",
                         selectforeground="#FFFFFF",
                         borderwidth=0,
                         highlightthickness=0,
                         font=("Segoe UI", 11))
    listbox.pack(side="left", expand=True, fill="both")
    listbox.bind("<<ListboxSelect>>", lambda event: on_item_select(event, name_entry, quantity_entry, price_entry))

    # --- Scrollbar ---
    scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=listbox.yview)
    scrollbar.pack(side="right", fill="y")
    listbox.config(yscrollcommand=scrollbar.set)

    refresh_listbox(listbox)

    root.mainloop()

if __name__ == "__main__":
    run_gui()
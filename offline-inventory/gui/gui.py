# gui.py (Tkinter for now)
import tkinter as tk
from tkinter import messagebox
import db.database as database


def refresh_listbox(listbox):
    listbox.delete(0, tk.END)
    for item in database.fetch_items():
        listbox.insert(tk.END, f"{item[0]} (x{item[1]}) - ${item[2]:.2f}")


def add_item(name_entry, quantity_entry, price_entry, listbox):
    name = name_entry.get()
    quantity = quantity_entry.get()
    price = price_entry.get()

    if not name or not quantity or not price:
        messagebox.showerror("Error", "All fields required")
        return

    try:
        database.insert_item(name, int(quantity), float(price))
        refresh_listbox(listbox)
    except ValueError:
        messagebox.showerror("Error", "Quantity must be int, Price must be float")


def run_gui():
    root = tk.Tk()
    root.title("Inventory System")

    tk.Label(root, text="Name").grid(row=0, column=0)
    tk.Label(root, text="Quantity").grid(row=1, column=0)
    tk.Label(root, text="Price").grid(row=2, column=0)

    name_entry = tk.Entry(root)
    quantity_entry = tk.Entry(root)
    price_entry = tk.Entry(root)

    name_entry.grid(row=0, column=1)
    quantity_entry.grid(row=1, column=1)
    price_entry.grid(row=2, column=1)

    listbox = tk.Listbox(root, width=50)
    listbox.grid(row=4, column=0, columnspan=2)

    tk.Button(
        root,
        text="Add Item",
        command=lambda: add_item(name_entry, quantity_entry, price_entry, listbox),
    ).grid(row=3, column=0, columnspan=2)

    refresh_listbox(listbox)

    root.mainloop()

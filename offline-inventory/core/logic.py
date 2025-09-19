# Talks to database.py.
# Handles rules like “quantity must be > 0” or “apply discount”.
import database

def add_new_item(name, quantity, price):
    if quantity <= 0:
        return "Error: Quantity must be positive."
    if price < 0:
        return "Error: Price cannot be negative."
    
    database.add_item(name, quantity, price)
    return "Item added successfully!"

def view_inventory():
    return database.get_all_items()

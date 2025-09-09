# inventory.py (OOP logic)
class Item:
    def __init__(self, name, quantity, price):
        self.name = name
        self.quantity = quantity
        self.price = price

    def __repr__(self):
        return f"{self.name} (x{self.quantity}) - ${self.price:.2f}"


class Inventory:
    def __init__(self):
        self.items = []

    def add_item(self, item):
        self.items.append(item)

    def remove_item(self, name):
        self.items = [item for item in self.items if item.name != name]

    def search_item(self, name):
        return [item for item in self.items if name.lower() in item.name.lower()]

    def get_all_items(self):
        return self.items

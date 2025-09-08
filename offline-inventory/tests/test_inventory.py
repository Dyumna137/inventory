
# tests/test_inventory.py

import pytest
from core.inventory import Inventory, Item


@pytest.fixture
def sample_inventory():
    inv = Inventory()
    inv.add_item(Item("Laptop", 5, 80000))
    inv.add_item(Item("Mouse", 10, 500))
    return inv


def test_add_item(sample_inventory):
    assert "Laptop" in sample_inventory.items
    assert sample_inventory.items["Laptop"].quantity == 5
    assert sample_inventory.items["Mouse"].price == 500


def test_update_quantity(sample_inventory):
    sample_inventory.update_quantity("Laptop", 3)
    assert sample_inventory.items["Laptop"].quantity == 3


def test_remove_item(sample_inventory):
    sample_inventory.remove_item("Mouse")
    assert "Mouse" not in sample_inventory.items


def test_total_value(sample_inventory):
    total = sample_inventory.total_value()
    expected = (5 * 80000) + (10 * 500)
    assert total == expected


def test_item_not_found(sample_inventory):
    with pytest.raises(KeyError):
        sample_inventory.update_quantity("Keyboard", 2)



"""
⚙️ How this works

pytest.fixture → creates a sample inventory with pre-added items (Laptop, Mouse).
Each test checks one feature:

✅ Adding items
✅ Updating quantity
✅ Removing items
✅ Total value calculation
✅ Handling invalid input (item not found → raises KeyError)
"""

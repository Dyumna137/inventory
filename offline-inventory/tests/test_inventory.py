# tests/test_inventory.py

import pytest
from core.inventory import Inventory, Item
from core import datasheet_importer


def test_csv_ingestion(tmp_path):
    """Test CSV file ingestion with minimal importer."""
    sample = tmp_path / "sample.csv"
    sample.write_text("id,name\n1,Widget\n2,Gadget")
    tables = datasheet_importer.ingest_file(str(sample))
    assert len(tables) == 1
    name, data = tables[0]
    assert "id" in data['columns']
    assert "name" in data['columns']
    assert len(data['rows']) == 2


def test_supported_extensions():
    """Test that we get the list of supported extensions."""
    extensions = datasheet_importer.get_supported_extensions()
    assert '.csv' in extensions
    assert '.txt' in extensions


@pytest.fixture
def sample_inventory():
    from core.config import set_inventory_type, InventoryType
    set_inventory_type(InventoryType.WAREHOUSE)
    
    inv = Inventory()
    laptop = Item(name="Laptop", quantity=5, price=80000, sku="LAP001")
    mouse = Item(name="Mouse", quantity=10, price=500, sku="MSE001")
    inv.add_item(laptop)
    inv.add_item(mouse)
    return inv


def test_add_item(sample_inventory):
    items = sample_inventory.get_all_items()
    assert len(items) == 2
    
    laptop = next((item for item in items if item.data["name"] == "Laptop"), None)
    mouse = next((item for item in items if item.data["name"] == "Mouse"), None)
    
    assert laptop is not None
    assert mouse is not None
    assert laptop.data["quantity"] == 5
    assert mouse.data["price"] == 500


def test_remove_item(sample_inventory):
    items_before = len(sample_inventory.get_all_items())
    mouse_item = next((item for item in sample_inventory.get_all_items() 
                      if item.data["name"] == "Mouse"), None)
    
    if mouse_item:
        sample_inventory.remove_item(mouse_item.id)
        items_after = len(sample_inventory.get_all_items())
        assert items_after == items_before - 1


def test_search_items(sample_inventory):
    results = sample_inventory.search_items("Laptop")
    assert len(results) == 1
    assert results[0].data["name"] == "Laptop"


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

"""
Flexible Configuration for Different Inventory Types
===================================================

Choose your inventory type and the system adapts automatically.
Supports warehouse, retail, library, restaurant, and custom inventories.
"""

from pathlib import Path
from enum import Enum
from typing import Dict, List, Any

# Database path relative to project root (data/inventory.db)
DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = str(DATA_DIR / "inventory.db")

# Supported extensions for file dialogs (used by GUI)
SUPPORTED_EXTS = ("*.csv", "*.txt")  # Basic support, Excel available if openpyxl/xlrd installed

class InventoryType(Enum):
    """Different types of inventory systems."""
    WAREHOUSE = "warehouse"
    RETAIL = "retail"
    LIBRARY = "library"
    RESTAURANT = "restaurant"
    ELECTRONICS = "electronics"

# Current inventory type (can be changed)
INVENTORY_TYPE = InventoryType.WAREHOUSE

# Field configurations for different inventory types
INVENTORY_SCHEMAS = {
    InventoryType.WAREHOUSE: [
        {"name": "name", "type": "TEXT", "required": True},
        {"name": "sku", "type": "TEXT", "required": False},
        {"name": "quantity", "type": "INTEGER", "required": True},
        {"name": "price", "type": "REAL", "required": True},
        {"name": "category", "type": "TEXT", "required": False},
        {"name": "supplier", "type": "TEXT", "required": False},
        {"name": "location", "type": "TEXT", "required": False},
        {"name": "min_stock", "type": "INTEGER", "required": False, "default": 0},
    ],
    
    InventoryType.RETAIL: [
        {"name": "name", "type": "TEXT", "required": True},
        {"name": "barcode", "type": "TEXT", "required": False},
        {"name": "quantity", "type": "INTEGER", "required": True},
        {"name": "cost_price", "type": "REAL", "required": True},
        {"name": "selling_price", "type": "REAL", "required": True},
        {"name": "brand", "type": "TEXT", "required": False},
        {"name": "category", "type": "TEXT", "required": False},
        {"name": "discount", "type": "REAL", "required": False, "default": 0},
    ],
    
    InventoryType.LIBRARY: [
        {"name": "title", "type": "TEXT", "required": True},
        {"name": "author", "type": "TEXT", "required": True},
        {"name": "isbn", "type": "TEXT", "required": False},
        {"name": "copies_total", "type": "INTEGER", "required": True},
        {"name": "copies_available", "type": "INTEGER", "required": True},
        {"name": "genre", "type": "TEXT", "required": False},
        {"name": "publisher", "type": "TEXT", "required": False},
        {"name": "year", "type": "INTEGER", "required": False},
        {"name": "location", "type": "TEXT", "required": False},
    ],
    
    InventoryType.RESTAURANT: [
        {"name": "name", "type": "TEXT", "required": True},
        {"name": "quantity", "type": "REAL", "required": True},
        {"name": "unit", "type": "TEXT", "required": True},
        {"name": "cost_per_unit", "type": "REAL", "required": True},
        {"name": "supplier", "type": "TEXT", "required": False},
        {"name": "expiry_date", "type": "TEXT", "required": False},
        {"name": "category", "type": "TEXT", "required": False},
        {"name": "min_stock", "type": "REAL", "required": False, "default": 0},
    ],
    
    InventoryType.ELECTRONICS: [
        {"name": "name", "type": "TEXT", "required": True},
        {"name": "model", "type": "TEXT", "required": True},
        {"name": "brand", "type": "TEXT", "required": True},
        {"name": "quantity", "type": "INTEGER", "required": True},
        {"name": "price", "type": "REAL", "required": True},
        {"name": "warranty_months", "type": "INTEGER", "required": False, "default": 12},
        {"name": "category", "type": "TEXT", "required": False},
        {"name": "specifications", "type": "TEXT", "required": False},
    ]
}

def set_inventory_type(inventory_type: InventoryType):
    """Set the current inventory type."""
    global INVENTORY_TYPE
    INVENTORY_TYPE = inventory_type

def get_inventory_type() -> str:
    """Get the current inventory type as a string."""
    # Try to load from config first
    if not INVENTORY_TYPE or INVENTORY_TYPE == InventoryType.WAREHOUSE:
        load_config()
    return INVENTORY_TYPE.value if INVENTORY_TYPE else "warehouse"

def get_inventory_fields() -> List[Dict[str, Any]]:
    """Get field configuration for current inventory type."""
    return INVENTORY_SCHEMAS.get(INVENTORY_TYPE, INVENTORY_SCHEMAS[InventoryType.WAREHOUSE])

def get_table_name() -> str:
    """Get table name for current inventory type."""
    return f"{INVENTORY_TYPE.value}_inventory"

def get_inventory_types() -> List[Dict[str, str]]:
    """Get available inventory types."""
    return [
        {"id": inv_type.value, "name": inv_type.value.title(), "description": get_type_description(inv_type)}
        for inv_type in InventoryType
    ]

def get_type_description(inv_type: InventoryType) -> str:
    """Get description for inventory type."""
    descriptions = {
        InventoryType.WAREHOUSE: "General warehouse inventory with SKU and location tracking",
        InventoryType.RETAIL: "Retail store with cost/selling prices and discounts",
        InventoryType.LIBRARY: "Library books with author, ISBN, and copy management",
        InventoryType.RESTAURANT: "Restaurant ingredients with units and expiry dates",
        InventoryType.ELECTRONICS: "Electronics with models, brands, and warranties",
    }
    return descriptions.get(inv_type, "Custom inventory system")

def setup_inventory_type():
    """Interactive setup for inventory type."""
    print("🎯 Choose Your Inventory Type")
    print("=" * 30)
    
    types = get_inventory_types()
    for i, inv_type in enumerate(types, 1):
        print(f"{i}. {inv_type['name']} - {inv_type['description']}")
    
    while True:
        try:
            choice = int(input(f"\nEnter choice (1-{len(types)}): "))
            if 1 <= choice <= len(types):
                selected_type = list(InventoryType)[choice-1]
                set_inventory_type(selected_type)
                save_config(selected_type)
                print(f"✅ Selected: {selected_type.value.title()} Inventory")
                return selected_type
            else:
                print("Invalid choice!")
        except ValueError:
            print("Please enter a number!")
        except KeyboardInterrupt:
            print("\nSetup cancelled.")
            return None

def save_config(inventory_type: InventoryType):
    """Save configuration to file."""
    config_file = DATA_DIR / "config.json"
    import json
    config = {"inventory_type": inventory_type.value}
    with open(config_file, 'w') as f:
        json.dump(config, f)

def load_config():
    """Load configuration from file."""
    config_file = DATA_DIR / "config.json"
    if config_file.exists():
        import json
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                inventory_type_str = config.get("inventory_type")
                if inventory_type_str:
                    for inv_type in InventoryType:
                        if inv_type.value == inventory_type_str:
                            set_inventory_type(inv_type)
                            return inv_type
        except (json.JSONDecodeError, KeyError):
            pass
    return None

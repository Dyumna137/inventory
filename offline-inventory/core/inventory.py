"""
Flexible Inventory System
========================

Works with any inventory configuration - warehouse, retail, library, restaurant, etc.
Items adapt automatically based on the chosen inventory type.

Author: [Your Team Name]
Version: 2.0.0
"""

import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any
from decimal import Decimal

from core.config import get_inventory_fields, INVENTORY_TYPE


class Item:
    """Flexible item that adapts to any inventory configuration."""
    
    def __init__(self, **kwargs):
        """Initialize item with flexible fields based on current config."""
        self.id = str(uuid.uuid4())[:8]
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
        # Get current inventory configuration
        fields = get_inventory_fields()
        
        # Set values for all configured fields
        self.data = {}
        
        for field_config in fields:
            field_name = field_config["name"]
            
            if field_name in kwargs:
                # Use provided value
                value = kwargs[field_name]
                # Convert to appropriate type if needed
                if field_config["type"] == "number" and isinstance(value, str):
                    value = int(value) if value.isdigit() else 0
                elif field_config["type"] == "decimal" and not isinstance(value, Decimal):
                    value = Decimal(str(value))
                self.data[field_name] = value
            elif field_config["required"]:
                raise ValueError(f"Required field '{field_name}' is missing")
            else:
                # Use default value if provided
                self.data[field_name] = field_config.get("default", None)
        
        # Validate required fields
        self._validate()
    
    def __getattr__(self, name):
        """Allow accessing data fields as attributes."""
        if name in self.data:
            return self.data[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def __setattr__(self, name, value):
        """Allow setting data fields as attributes."""
        if name in ['id', 'created_at', 'updated_at', 'data']:
            super().__setattr__(name, value)
        elif hasattr(self, 'data') and name in [field["name"] for field in get_inventory_fields()]:
            self.data[name] = value
            self.updated_at = datetime.now()
        else:
            super().__setattr__(name, value)
    
    def _validate(self):
        """Validate item data based on configuration."""
        fields = get_inventory_fields()
        
        for field_config in fields:
            field_name = field_config["name"]
            value = self.data.get(field_name)
            
            if field_config["required"] and (value is None or value == ""):
                raise ValueError(f"Required field '{field_name}' cannot be empty")
            
            if value is not None and field_config["type"] == "number" and value < 0:
                raise ValueError(f"Field '{field_name}' cannot be negative")
    
    def update_field(self, field_name: str, new_value: Any):
        """Update a specific field with validation."""
        fields = get_inventory_fields()
        field_config = next((f for f in fields if f["name"] == field_name), None)
        
        if not field_config:
            raise ValueError(f"Field '{field_name}' is not configured for this inventory type")
        
        # Type conversion
        if field_config["type"] == "number" and not isinstance(new_value, (int, float)):
            new_value = int(new_value) if str(new_value).isdigit() else 0
        elif field_config["type"] == "decimal" and not isinstance(new_value, Decimal):
            new_value = Decimal(str(new_value))
        
        self.data[field_name] = new_value
        self.updated_at = datetime.now()
        self._validate()
    
    @property
    def total_value(self) -> Decimal:
        """Calculate total value if price and quantity fields exist."""
        price = self.data.get("price", Decimal('0'))
        quantity = self.data.get("quantity", 0)
        if isinstance(price, (int, float)):
            price = Decimal(str(price))
        return price * quantity
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert item to dictionary."""
        result = {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
        
        # Add all data fields
        for key, value in self.data.items():
            if isinstance(value, Decimal):
                result[key] = float(value)
            else:
                result[key] = value
        
        return result
    
    def __repr__(self):
        name = self.data.get("name", "Unknown Item")
        return f"{name} (ID: {self.id})"


class Inventory:
    """Flexible inventory management system."""
    
    def __init__(self):
        self.items: Dict[str, Item] = {}  # id -> Item mapping
    
    def add_item(self, item: Item) -> bool:
        """Add item to inventory."""
        self.items[item.id] = item
        return True
    
    def remove_item(self, item_id: str) -> bool:
        """Remove item from inventory."""
        if item_id in self.items:
            del self.items[item_id]
            return True
        return False
    
    def get_item(self, item_id: str) -> Optional[Item]:
        """Get item by ID."""
        return self.items.get(item_id)
    
    def get_all_items(self) -> List[Item]:
        """Get all items."""
        return list(self.items.values())
    
    def search_items(self, query: str) -> List[Item]:
        """Search items by name or other searchable fields."""
        if not query:
            return self.get_all_items()
        
        query = query.lower()
        results = []
        
        for item in self.items.values():
            # Search in all text fields
            for field_name, value in item.data.items():
                if isinstance(value, str) and query in value.lower():
                    results.append(item)
                    break
        
        return results
    
    def filter_items(self, **filters) -> List[Item]:
        """Filter items by field values."""
        results = list(self.items.values())
        
        for field_name, filter_value in filters.items():
            results = [item for item in results 
                      if item.data.get(field_name) == filter_value]
        
        return results
    
    def total_value(self) -> Decimal:
        """Calculate total inventory value."""
        return sum(item.total_value for item in self.items.values())
    
    def export_to_json(self, file_path: str):
        """Export inventory to JSON file."""
        data = {
            'export_date': datetime.now().isoformat(),
            'inventory_type': INVENTORY_TYPE,
            'total_items': len(self.items),
            'total_value': float(self.total_value()),
            'items': [item.to_dict() for item in self.items.values()]
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def import_from_json(self, file_path: str):
        """Import inventory from JSON file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        for item_data in data.get('items', []):
            # Remove metadata fields
            item_data.pop('id', None)
            item_data.pop('created_at', None)
            item_data.pop('updated_at', None)
            
            item = Item(**item_data)
            self.add_item(item)
    
    def __len__(self):
        return len(self.items)
    
    def __contains__(self, item_id: str):
        return item_id in self.items
    
    def __iter__(self):
        return iter(self.items.values())

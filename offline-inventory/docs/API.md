# API Documentation

## 📚 **Core Module APIs**

### **Configuration Module (`core/config.py`)**

#### **Primary Functions**

```python
def get_inventory_fields() -> List[Dict[str, Any]]
```
**Purpose**: Returns field configuration for current inventory type
**Returns**: List of field definitions with name, type, required status
**Usage**: Dynamic form generation and validation

```python
def setup_inventory_type() -> None
```
**Purpose**: Interactive setup for choosing inventory type
**Side Effects**: Updates global configuration, saves to preferences
**Usage**: First-time system setup

```python
def get_inventory_type() -> str
```
**Purpose**: Get currently configured inventory type
**Returns**: String identifier (warehouse, retail, library, etc.)
**Usage**: System initialization and display

#### **Configuration Schema Structure**
```python
{
    "name": "field_name",       # Database field name
    "type": "text|number|decimal|date",  # Data type
    "required": True|False,     # Validation requirement
    "default": "value"          # Optional default value
}
```

### **Inventory Module (`core/inventory.py`)**

#### **Item Class**

```python
class Item:
    def __init__(self, **kwargs)
```
**Purpose**: Create flexible inventory item
**Parameters**: Dynamic based on current configuration
**Validation**: Automatic based on field definitions

**Key Methods:**

```python
def update_field(self, field_name: str, new_value: Any) -> None
```
**Purpose**: Update specific field with validation
**Parameters**: 
- `field_name`: Name of field to update
- `new_value`: New value (type-converted automatically)
**Raises**: ValueError for validation failures

```python
def to_dict(self) -> Dict[str, Any]
```
**Purpose**: Convert item to dictionary for storage/serialization
**Returns**: Dictionary with all item data including metadata
**Usage**: Database operations, export functionality

#### **Inventory Class**

```python
class Inventory:
    def add_item(self, item: Item) -> bool
```
**Purpose**: Add item to inventory collection
**Parameters**: Item object to add
**Returns**: True if added successfully
**Side Effects**: Updates internal storage

```python
def search_items(self, query: str) -> List[Item]
```
**Purpose**: Search items by text query
**Parameters**: Search string (searches all text fields)
**Returns**: List of matching items
**Algorithm**: Case-insensitive partial matching

```python
def get_all_items(self) -> List[Item]
```
**Purpose**: Retrieve all items in inventory
**Returns**: List of all Item objects
**Usage**: Display operations, bulk operations

## 🗄️ **Database Module API (`db/database.py`)**

### **Database Class**

```python
class Database:
    def __init__(self, db_path: str = "data/inventory.db")
```
**Purpose**: Initialize database connection
**Parameters**: Path to SQLite database file
**Side Effects**: Creates database file and tables if not exist

**Key Methods:**

```python
def save_item(self, item_dict: Dict[str, Any]) -> bool
```
**Purpose**: Persist item to database
**Parameters**: Item dictionary (from `item.to_dict()`)
**Returns**: Success status
**Storage Format**: JSON in flexible schema

```python
def get_all_items(self) -> List[Dict[str, Any]]
```
**Purpose**: Retrieve all items from database
**Returns**: List of item dictionaries
**Error Handling**: Returns empty list on database errors

```python
def delete_item(self, item_id: str) -> bool
```
**Purpose**: Remove item from database
**Parameters**: Unique item identifier
**Returns**: Success status

## 🖥️ **GUI Module API (`gui/gui.py`)**

### **Key Functions**

```python
def create_input_fields(parent_frame: ttk.Frame) -> None
```
**Purpose**: Generate form fields based on current configuration
**Parameters**: Tkinter frame to contain fields
**Side Effects**: Updates global `field_entries` dictionary
**Algorithm**: Reads configuration and creates appropriate widgets

```python
def add_item(listbox: tk.Listbox) -> None
```
**Purpose**: Handle new item creation from GUI
**Parameters**: Listbox widget to update after creation
**Workflow**: Validate → Create → Save → Refresh → Clear form
**Error Handling**: Shows user-friendly error messages

```python
def refresh_listbox(listbox: tk.Listbox) -> None
```
**Purpose**: Update item display list
**Parameters**: Listbox widget to refresh
**Data Source**: Current inventory collection
**Format**: Displays first 3 configured fields per item

### **Event Handlers**

```python
def on_item_select(event, listbox: tk.Listbox) -> None
```
**Purpose**: Handle item selection in list
**Parameters**: Event object and listbox widget
**Side Effects**: Populates form fields with selected item data
**Usage**: Edit workflow initialization

## 🔧 **Integration APIs**

### **Configuration-GUI Integration**

The GUI automatically adapts based on configuration:

```python
# Configuration drives GUI
fields = get_inventory_fields()
for field in fields:
    widget = create_widget_for_field(field)
    # Widget type, validation, labels all from config
```

### **Inventory-Database Integration**

Items flow seamlessly between layers:

```python
# Create → Store → Retrieve workflow
item = Item(**form_data)          # Core layer
inventory.add_item(item)          # Business layer  
database.save_item(item.to_dict()) # Data layer
```

## 🎯 **Usage Patterns**

### **Adding New Inventory Type**

1. **Define Configuration**:
```python
INVENTORY_SCHEMAS[InventoryType.CUSTOM] = [
    {"name": "custom_field", "type": "text", "required": True}
]
```

2. **System Automatically**:
   - Creates appropriate GUI fields
   - Handles validation
   - Stores data correctly
   - Searches all fields

### **Extending Functionality**

```python
# Add new field type
def handle_new_field_type(field_config, value):
    if field_config["type"] == "custom_type":
        return custom_validation(value)
    return default_validation(value)
```

This API design demonstrates **professional software architecture** with clear separation of concerns, consistent interfaces, and comprehensive error handling.
# 🎯 Flexible Inventory Management System

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Architecture](https://img.shields.io/badge/Architecture-Clean-green.svg)](./docs/ARCHITECTURE.md)
[![Documentation](https://img.shields.io/badge/Docs-Comprehensive-blue.svg)](./docs/)

**A Professional, Adaptable Inventory Management System** - Demonstrates advanced software engineering principles through flexible architecture that adapts to different business requirements without code duplication.

## 🎯 **Project Purpose & Academic Value**

### **Why This System Exists**
This project showcases **professional software development practices** by solving a real-world problem: different businesses need different inventory management approaches, but creating separate systems leads to code duplication and maintenance issues.

### **What It Demonstrates**
- **Clean Architecture**: Proper separation of concerns
- **Design Patterns**: Configuration pattern, Factory pattern, Observer pattern
- **Professional Practices**: Virtual environments, comprehensive documentation, testing
- **Flexible Design**: One codebase serves multiple business types
- **Industry Standards**: Code organization, documentation, and development workflow

## 🏪 **Business Applications**

### 🏭 **Warehouse Management**
```
✅ Fields: Name, SKU, Quantity, Location, Price
✅ Features: Location tracking, stock levels, supplier management
✅ Perfect For: Distribution centers, storage facilities
```

### 🛒 **Retail Store**
```
✅ Fields: Name, Category, Cost Price, Selling Price, Supplier
✅ Features: Profit margin tracking, inventory valuation
✅ Perfect For: Small to medium retail businesses
```

### 📚 **Library System**
```
✅ Fields: Title, Author, ISBN, Copies Available, Genre
✅ Features: Book catalog, availability tracking, author management
✅ Perfect For: Schools, public libraries, bookstores
```

### 🍽️ **Restaurant Inventory**
```
✅ Fields: Ingredient, Unit, Quantity, Expiry Date, Supplier
✅ Features: Expiry management, unit tracking, supplier info
✅ Perfect For: Restaurants, cafes, catering services
```

### 💻 **Electronics Store**
```
✅ Fields: Product, Brand, Model, Warranty, Price
✅ Features: Warranty tracking, brand management, model specs
✅ Perfect For: Electronics retailers, repair shops
```

## 🏗️ **Professional Architecture**

### **System Design**
```
📁 inventory-system/
├── 🎯 core/                    # Business Logic Layer
│   ├── config.py               # Configuration schemas & management
│   ├── inventory.py            # Domain models (Item, Inventory)
│   └── datasheet_importer.py   # Data import utilities (extensible)
├── 🖥️ gui/                     # Presentation Layer
│   └── gui.py                  # Dynamic Tkinter interface
├── 🗄️ db/                      # Data Access Layer
│   └── database.py             # SQLite with flexible JSON storage
├── 📋 data/                    # Data Storage
│   └── inventory.db            # SQLite database (auto-created)
├── 🧪 tests/                   # Test Suite
│   ├── test_inventory.py       # Unit tests for business logic
│   └── test_database_importer.py # Integration tests
├── 📚 docs/                    # Comprehensive Documentation
│   ├── ARCHITECTURE.md         # System design & patterns used
│   ├── WORKFLOW.md             # How the system works
│   ├── API.md                  # Code documentation
│   └── DEVELOPMENT.md          # Setup & contribution guide
├── 🐍 venv/                    # Virtual Environment (best practice)
├── 📄 requirements.txt         # Dependency management
└── 🚀 convenience scripts      # Easy execution helpers
```

### **Key Design Patterns**
1. **Configuration Pattern**: Behavior driven by data, not code
2. **Factory Pattern**: Items created through flexible configuration
3. **Observer Pattern**: GUI updates automatically when data changes
4. **Separation of Concerns**: Clear boundaries between layers

## 🚀 **Quick Start Guide**

### **Installation & Setup**
```bash
# 1. Create virtual environment (professional practice)
python -m venv venv

# 2. Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows CMD:
venv\Scripts\activate.bat

# 3. Run setup (first time only)
python main.py --setup

# 4. Launch system
python main.py
```

### **Using Convenience Scripts**
```bash
# Windows users can simply double-click:
run.bat      # Automatically activates venv and runs system
setup.ps1    # Runs setup process in PowerShell
```

## 🔄 **How It Works**

### **System Workflow**
1. **Configuration**: User selects inventory type (one-time setup)
2. **Dynamic Adaptation**: System configures itself automatically
3. **Runtime**: GUI, database, and business logic adapt to chosen type
4. **Operations**: User manages inventory through adaptive interface

### **Technical Flow**
```
User Choice → Configuration Loading → Database Schema → GUI Generation → Business Logic
```

### **Data Flow**
```
User Input → Validation → Domain Models → Database Storage → GUI Updates
```

## 💡 **Usage Examples**

### **Academic Demonstration**
```python
# Show how same code works for different businesses
python main.py --setup  # Choose "Library"
# System now manages books with ISBN, authors, etc.

python main.py --setup  # Choose "Warehouse" 
# Same system now manages products with SKU, locations, etc.
```

### **Development Workflow**
```python
# Add new inventory type without changing existing code
INVENTORY_SCHEMAS[InventoryType.PHARMACY] = [
    {"name": "medicine_name", "type": "text", "required": True},
    {"name": "dosage", "type": "text", "required": True},
    {"name": "expiry_date", "type": "date", "required": True}
]
# System automatically supports pharmacy inventory!
```

## 📚 **Documentation**

### **For Developers**
- **[Architecture Guide](./docs/ARCHITECTURE.md)**: System design and patterns
- **[API Documentation](./docs/API.md)**: Code documentation and usage
- **[Workflow Guide](./docs/WORKFLOW.md)**: How everything works together

### **For Users**
- **[Setup Guide](./VENV_GUIDE.md)**: Virtual environment and installation
- **[User Manual](./docs/USER_GUIDE.md)**: How to use the system

### **For Instructors**
- **[Academic Value](./docs/ACADEMIC.md)**: What this project demonstrates
- **[Assessment Criteria](./docs/ASSESSMENT.md)**: Professional standards shown

## 🎓 **Academic & Professional Value**

### **Software Engineering Principles Demonstrated**
- ✅ **SOLID Principles**: Single responsibility, Open/closed, etc.
- ✅ **Clean Architecture**: Clear layer separation
- ✅ **Design Patterns**: Multiple patterns properly implemented
- ✅ **Professional Practices**: Version control, documentation, testing

### **Real-World Skills Shown**
- ✅ **Problem Analysis**: Identifying common patterns across domains
- ✅ **Flexible Design**: Creating adaptable solutions
- ✅ **Code Quality**: Clean, maintainable, well-documented code
- ✅ **Team Collaboration**: Structure that supports multiple developers

### **Industry Standards**
- ✅ **Virtual Environments**: Proper dependency isolation
- ✅ **Project Structure**: Professional organization
- ✅ **Documentation**: Comprehensive and maintainable
- ✅ **Error Handling**: Robust and user-friendly

## 🔧 **Technical Specifications**

### **Requirements**
- **Python**: 3.8+ (uses standard library only)
- **Database**: SQLite (included with Python)
- **GUI**: Tkinter (included with Python)
- **Dependencies**: None for core functionality

### **Features**
- **Zero Dependencies**: Uses only Python standard library
- **Portable**: Single file database, runs anywhere
- **Lightweight**: Minimal resource usage
- **Extensible**: Easy to add new inventory types
- **Professional**: Industry-standard code organization

## 🤝 **Contributing & Extension**

### **Adding New Inventory Types**
1. Define field configuration in `core/config.py`
2. System automatically adapts - no other changes needed
3. Test with existing test suite

### **Adding Features**
1. Follow existing architecture patterns
2. Update documentation
3. Add appropriate tests

### **Code Standards**
- Follow PEP 8 style guidelines
- Add docstrings to all functions
- Update documentation for changes
- Maintain backwards compatibility

## 🎯 **Project Goals Achieved**

✅ **Professional Team Project Appearance**: Clean structure, documentation, standards  
✅ **Versatile Without Complexity**: One system, multiple uses, simple design  
✅ **No Duplicate Code**: Single codebase adapts through configuration  
✅ **Industry Best Practices**: Virtual environments, proper architecture, documentation  
✅ **Academic Value**: Demonstrates advanced software engineering concepts  
✅ **Real-World Applicable**: Solves actual business problems  

This system demonstrates that **good software engineering** creates solutions that are both **professionally robust** and **academically valuable**.
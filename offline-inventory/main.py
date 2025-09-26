"""
Flexible Inventory Management System
===================================

Adaptive inventory system that works for any business type.

Usage:
    python main.py                    # Launch the flexible GUI
    python main.py --setup           # Run inventory type setup
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.config import setup_inventory_type, get_inventory_type
from gui.gui import run_gui


def main():
    """Main entry point for the flexible inventory system."""
    parser = argparse.ArgumentParser(description="Flexible Inventory Management System")
    parser.add_argument('--setup', action='store_true', 
                      help='Run inventory type setup')
    
    args = parser.parse_args()
    
    try:
        if args.setup:
            # Run setup process
            setup_inventory_type()
            print("✅ Setup complete! You can now run the system without --setup")
        else:
            # Check if inventory type is configured
            inventory_type = get_inventory_type()
            if not inventory_type:
                print("🔧 First time setup required...")
                setup_inventory_type()
                inventory_type = get_inventory_type()
            
            print(f"🏪 Starting {inventory_type.title()} Inventory System")
            run_gui()
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
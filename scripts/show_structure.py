#!/usr/bin/env python3
"""
Project structure visualization script.
"""

import os
from pathlib import Path


def print_tree(directory, prefix="", max_depth=3, current_depth=0):
    """Print directory tree structure."""
    if current_depth > max_depth:
        return
    
    directory = Path(directory)
    if not directory.exists():
        return
    
    # Get all items in directory
    items = sorted([
        item for item in directory.iterdir() 
        if not item.name.startswith('.') and item.name != '__pycache__'
    ])
    
    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        current_prefix = "└── " if is_last else "├── "
        print(f"{prefix}{current_prefix}{item.name}")
        
        if item.is_dir() and current_depth < max_depth:
            extension = "    " if is_last else "│   "
            print_tree(item, prefix + extension, max_depth, current_depth + 1)


def main():
    """Main function."""
    print("🏸 Badminton League Auction System - Project Structure")
    print("=" * 60)
    print()
    
    project_root = Path(__file__).parent.parent  # Go up one level from scripts/
    print(f"📁 {project_root.name}/")
    print_tree(project_root, max_depth=3)
    
    print()
    print("Key Components:")
    print("├── 🚀 app.py - Main application entry point")
    print("├── 📋 Makefile - Build automation and commands") 
    print("├── 🐳 Dockerfile - Container configuration")
    print("├── 📦 src/ - Source code modules")
    print("│   ├── 🔧 core/ - Business logic (database, auth, models)")
    print("│   ├── 🎨 ui/ - User interface components")
    print("│   └── 🛠️ utils/ - Utility functions")
    print("├── ⚙️ config/ - Configuration files")
    print("├── 📜 scripts/ - Utility scripts")
    print("├── 🧪 tests/ - Test suite")
    print("├── 📊 data/ - Initial CSV data")
    print("└── 🖼️ assets/ - Static assets (images, etc.)")


if __name__ == "__main__":
    main()

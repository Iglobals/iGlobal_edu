#!/usr/bin/env python3
"""
Migration script to add LibraryItem table
Run this after updating models.py
"""

from app import app
from extensions import db
from models import LibraryItem

def migrate():
    print("=" * 60)
    print("iGlobals - Library Migration")
    print("=" * 60)
    
    try:
        with app.app_context():
            print("\n📦 Creating library_items table...")
            db.create_all()
            print("   ✓ Table created successfully!")
            
            print("\n✅ Migration completed successfully!")
            print("\nYou can now use the new library features:")
            print("  - Added Books: Books added to library (not necessarily purchased)")
            print("  - Your Books: Free books + purchased books (full access)")
            print("  - Favorites: Subset of Your Books marked as favorites")
            
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Ensure PostgreSQL is running")
        print("  2. Check database connection in .env")
        print("  3. Verify models.py has LibraryItem class")
        return False
    
    return True

if __name__ == '__main__':
    migrate()

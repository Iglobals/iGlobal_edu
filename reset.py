#!/usr/bin/env python3
"""
Database Reset Script
This will DROP ALL TABLES and recreate them fresh
⚠️ WARNING: This will delete ALL data!
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

database_url = os.getenv('DATABASE_URL')
if not database_url:
    print("\n✗ DATABASE_URL not found")
    sys.exit(1)

print("=" * 60)
print("⚠️  DATABASE RESET SCRIPT")
print("=" * 60)
print("\nThis will DELETE ALL DATA from your database!")
print("Tables that will be affected:")
print("  - users")
print("  - books")
print("  - purchases")
print("  - reviews")
print("  - favorites")
print("  - notes")
print("  - library_items (and any other tables)")

response = input("\n❓ Are you ABSOLUTELY SURE? Type 'YES' to continue: ")

if response != 'YES':
    print("\n✓ Cancelled. No changes made.")
    sys.exit(0)

try:
    from app import app, db
    
    print("\n🗑️  Dropping all tables...")
    with app.app_context():
        db.drop_all()
        print("   ✓ All tables dropped")
        
        print("\n📦 Creating fresh tables...")
        db.create_all()
        print("   ✓ All tables created")
    
    print("\n" + "=" * 60)
    print("✅ DATABASE RESET COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Run setup: python3 setup.py")
    print("  2. Seed books: python3 seed_data.py")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    sys.exit(1)
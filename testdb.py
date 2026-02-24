#!/usr/bin/env python3
"""
Database Connection Diagnostic Script
This will help identify issues with the .env file and database connection
"""

import os
from dotenv import load_dotenv

print("=" * 60)
print("DATABASE CONNECTION DIAGNOSTICS")
print("=" * 60)

# Step 1: Check if .env file exists
env_path = '.env'
if os.path.exists(env_path):
    print(f"✓ .env file found at: {os.path.abspath(env_path)}")
else:
    print(f"✗ .env file NOT found at: {os.path.abspath(env_path)}")
    print("Please create a .env file in your project root")
    exit(1)

# Step 2: Load environment variables
print("\nLoading environment variables from .env...")
load_dotenv()

# Step 3: Check DATABASE_URL
database_url = os.getenv('DATABASE_URL')
print(f"\nDATABASE_URL from .env:")
if database_url:
    # Mask the password for security
    if '@' in database_url:
        parts = database_url.split('@')
        if ':' in parts[0]:
            user_pass = parts[0].split('://')[-1]
            user = user_pass.split(':')[0]
            masked_url = database_url.replace(user_pass.split(':')[1], '****')
            print(f"  {masked_url}")
        else:
            print(f"  {database_url}")
    else:
        print(f"  {database_url}")
else:
    print("  ✗ DATABASE_URL is not set in .env file")
    print("\nYour .env file should contain:")
    print("DATABASE_URL=postgresql://profeso1012:secured123@localhost:5432/iglobals_db")
    exit(1)

# Step 4: Try to connect
print("\nAttempting database connection...")
try:
    import psycopg2
    from urllib.parse import urlparse
    
    # Parse the DATABASE_URL
    result = urlparse(database_url)
    username = result.username
    password = result.password
    database = result.path[1:]
    hostname = result.hostname
    port = result.port
    
    print(f"  Host: {hostname}")
    print(f"  Port: {port}")
    print(f"  Database: {database}")
    print(f"  User: {username}")
    print(f"  Password: {'*' * len(password) if password else 'NOT SET'}")
    
    conn = psycopg2.connect(
        host=hostname,
        port=port,
        database=database,
        user=username,
        password=password
    )
    
    print("\n✓ Database connection successful!")
    
    # Test query
    cursor = conn.cursor()
    cursor.execute('SELECT version();')
    version = cursor.fetchone()
    print(f"✓ PostgreSQL version: {version[0]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"\n✗ Database connection failed: {e}")
    print("\nTroubleshooting steps:")
    print("1. Ensure PostgreSQL is running: sudo systemctl status postgresql")
    print("2. Verify database exists: psql -d postgres -c '\\l'")
    print("3. Check user password: psql -U profeso1012 -d iglobals_db")
    print("4. Verify .env file has correct credentials")
    exit(1)

print("\n" + "=" * 60)
print("All checks passed! Your database connection is working.")
print("=" * 60)
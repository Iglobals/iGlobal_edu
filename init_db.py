#!/usr/bin/env python
"""
Initialize database tables on Neon or any remote PostgreSQL instance
Run this once after deploying to Vercel
"""
import os
from dotenv import load_dotenv
from app import app, db

load_dotenv()

if __name__ == '__main__':
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("✓ Database tables created successfully!")

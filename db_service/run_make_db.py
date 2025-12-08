"""
Database Schema Creation Script.

This script creates all database tables in PostgreSQL using SQLAlchemy ORM models.
It uses the DATABASE_URL from environment variables to connect to the hosted PostgreSQL service.

Environment Variables Required:
    DATABASE_URL: PostgreSQL connection URL (format: postgresql://user:password@host:port/database)
    RECREATE_DB (optional): Set to "true" to drop and recreate all tables (default: "false")

Tables Created:
    - projects: Real estate project listings
    - leads: Customer leads and preferences  
    - bookings: Property bookings linking leads to projects
    - history: Conversation/chat history tracking

Usage:
    python run_make_db.py
"""

import asyncio
import sys
from config import settings
from service.create_tables import create_all_tables


def main():
    """Main function to create database schema."""
    
    print("\n" + "=" * 70)
    print("DATABASE SCHEMA CREATION")
    print("=" * 70)
    print(f"Database URL: {settings.database_url[:30]}...")
    print(f"Recreate DB: {settings.recreate_db}")
    print("=" * 70)
    print()
    
    if settings.recreate_db:
        print("⚠️  WARNING: RECREATE_DB is set to True!")
        print("⚠️  This will DROP ALL EXISTING TABLES and DATA!")
        print()
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Operation cancelled.")
            sys.exit(0)
        print()
    
    try:
        # Run async table creation
        asyncio.run(create_all_tables(settings.database_url, recreate=settings.recreate_db))
        
        print("\n" + "=" * 70)
        print("✅ DATABASE SCHEMA SETUP COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("\nNext steps:")
        print("  1. Run 'python run_seed_db.py' to populate the database with data")
        print("  2. Start your FastAPI application")
        print()
        
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"❌ ERROR: Database schema creation failed!")
        print(f"Error: {str(e)}")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()

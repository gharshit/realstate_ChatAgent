"""
Database Seeding Script.

This script seeds the PostgreSQL database with project data from a CSV file.
It uses SQLAlchemy async session to insert data efficiently.

Environment Variables Required:
    DATABASE_URL: PostgreSQL connection URL (format: postgresql://user:password@host:port/database)

Data Source:
    CSV file located at: seed_db/ProplensData.csv

Usage:
    python run_seed_db.py
"""

import asyncio
import sys
from config import settings
from service.insert_data_projects import insert_projects_data


def main():
    """Main function to seed database with project data."""
    
    print("\n" + "=" * 70)
    print("DATABASE SEEDING - PROJECTS DATA")
    print("=" * 70)
    print(f"Database URL: {settings.database_url[:30]}...")
    print(f"CSV Path: {settings.csv_path}")
    print("=" * 70)
    print()
    
    try:
        # Run async data insertion
        inserted_count, skipped_count = asyncio.run(
            insert_projects_data(settings.database_url, settings.csv_path)
        )
        
        print("\n" + "=" * 70)
        print("✅ DATABASE SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print(f"Total inserted: {inserted_count}")
        print(f"Total skipped: {skipped_count}")
        print()
        print("Database is now ready to use with your FastAPI application!")
        print("=" * 70)
        print()
        
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"❌ ERROR: Database seeding failed!")
        print(f"Error: {str(e)}")
        print("=" * 70)
        print("\nTroubleshooting:")
        print("  1. Ensure database tables are created (run 'python run_make_db.py')")
        print("  2. Check that CSV file exists at the specified path")
        print("  3. Verify DATABASE_URL is correctly set in .env file")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()

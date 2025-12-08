"""
Create all database tables using SQLAlchemy ORM models.

This module creates all database tables defined in dbmodels.py including:
- projects: Real estate project listings
- leads: Customer leads and preferences
- bookings: Property bookings linking leads to projects
- history: Conversation/chat history tracking

All tables are created with proper:
- Primary keys and auto-increment
- Foreign key constraints and relationships
- Indexes for query performance
- Timestamps with automatic updates
"""

import asyncio
import sys
from pathlib import Path
from sqlalchemy import text

# Add parent directory to path for imports when running as script
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from db_service.client.dbmodels import Base
from db_service.client.postgres_connection import create_temp_async_engine
from db_service.config import settings


async def create_all_tables(database_url: str, recreate: bool = False):
    """
    Create all database tables using SQLAlchemy ORM models.
    
    Args:
        database_url: PostgreSQL connection URL
        recreate: If True, drop all existing tables before creating new ones (CAUTION: data loss!)
    
    Returns:
        None
    """
    # Create temporary async engine using connection helper
    engine = create_temp_async_engine(database_url, echo=False)
    
    try:
        async with engine.begin() as conn:
            if recreate:
                print("=" * 70)
                print("WARNING: Dropping all existing tables...")
                print("=" * 70)
                # Drop all tables
                await conn.run_sync(Base.metadata.drop_all)
                print("✓ All tables dropped successfully.")
                print()
            
            print("=" * 70)
            print("Creating all tables...")
            print("=" * 70)
            
            # Create all tables defined in Base metadata
            await conn.run_sync(Base.metadata.create_all)
            
            print("✓ All tables created successfully:")
            print("  - projects (with indexes on name, bedrooms, city, price)")
            print("  - leads (with indexes on email, city, budget)")
            print("  - bookings (with foreign keys to leads and projects)")
            print("  - history (with foreign key to leads)")
            print()
            
            # Verify tables exist
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """))
            
            tables = [row[0] for row in result.fetchall()]
            print("=" * 70)
            print(f"Database tables verified: {', '.join(tables)}")
            print("=" * 70)
        
        print("\n✅ Database schema setup completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error creating tables: {str(e)}")
        raise
    finally:
        await engine.dispose()


async def drop_all_tables(database_url: str):
    """
    Drop all database tables (CAUTION: This will delete all data!)
    
    Args:
        database_url: PostgreSQL connection URL
    
    Returns:
        None
    """
    # Create temporary async engine using connection helper
    engine = create_temp_async_engine(database_url, echo=False)
    
    try:
        async with engine.begin() as conn:
            print("=" * 70)
            print("DROPPING ALL TABLES...")
            print("=" * 70)
            await conn.run_sync(Base.metadata.drop_all)
            print("✓ All tables dropped successfully.")
    except Exception as e:
        print(f"❌ Error dropping tables: {str(e)}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    
    # Run table creation
    asyncio.run(create_all_tables(settings.database_url, recreate=settings.recreate_db))

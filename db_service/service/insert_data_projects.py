"""
Seed Projects Data from CSV into PostgreSQL Database.

This module reads project data from a CSV file and inserts it into the
PostgreSQL database using SQLAlchemy async session and ORM models.

Features:
- CSV to database mapping
- Data validation and type conversion
- Duplicate detection and skipping
- Progress reporting
- Error handling and rollback
"""

import asyncio
import csv
import sys
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select

# Add parent directory to path for imports when running as script
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from db_service.client.dbmodels import Project
from db_service.client.postgres_connection import create_temp_async_engine
from db_service.config import settings


##?======================= PREPROCESSING STEPS ===================================
##> Column mapping from CSV to database
COLUMN_MAPPING = {
    'Project name'                          : 'project_name',
    'No of bedrooms'                        : 'no_of_bedrooms',
    'Completion status (off plan/available)': 'completion_status',
    'bathrooms'                             : 'bathrooms',
    'unit type'                             : 'unit_type',
    'developer name'                        : 'developer_name',
    'Price (USD)'                           : 'price_usd',
    'Area (sq mtrs)'                        : 'area_sq_mtrs',
    'Property type (apartment/villa)'       : 'property_type',
    'city'                                  : 'city',
    'country'                               : 'country',
    'completion_date'                       : 'completion_date',
    'features'                              : 'features',
    'facilities'                            : 'facilities',
    'Project description'                   : 'project_description'
}


##> Helper function to clean completion status
def clean_completion_status(status: str) -> str:
    """Remove 'x_' prefix from completion status if present."""
    if status and status.startswith('x_'):
        return status[2:]
    return status


##> Helper function to convert value to appropriate type
def convert_value(value: str, column_name: str):
    """Convert CSV string value to appropriate database type."""
    if value is None or value.strip() == '':
        return None
    
    # Integer columns
    if column_name in ['no_of_bedrooms', 'bathrooms']:
        try:
            return int(float(value)) if value else None
        except (ValueError, TypeError):
            return None
    
    # Real/Float columns
    if column_name in ['price_usd', 'area_sq_mtrs']:
        try:
            return float(value) if value else None
        except (ValueError, TypeError):
            return None
    
    # List columns (stored as JSON in PostgreSQL)
    if column_name in ['features', 'facilities']:
        if value and value.strip():
            # Split by comma and clean up each item
            items = [item.strip() for item in value.split(',') if item.strip()]
            return items if items else None
        return None
    
    # Text columns - return as is
    return value.strip() if value else None


##> Helper function to validate required fields
def is_valid_row(data: dict) -> bool:
    """
    Check if row has all required fields and valid completion status.
    
    Args:
        data: Dictionary containing row data
    
    Returns:
        True if row is valid, False otherwise
    """
    ##> Check if required fields are not null
    required_fields = ['project_name', 'no_of_bedrooms', 'price_usd', 'city']
    for field in required_fields:
        if data.get(field) is None:
            return False
    
    ##> Check if completion status is valid (must be 'offplan' or 'available')
    completion_status = data.get('completion_status')
    if completion_status and completion_status.lower() not in ['offplan', 'available']:
        return False
    
    return True

##?======================================================================================


##?======================= INSERT DATA STEPS ===========================================

async def insert_projects_data(database_url: str, csv_path: str) -> tuple[int, int]:
    """
    Read CSV file and insert data into projects table using SQLAlchemy async.
    
    Args:
        database_url: PostgreSQL connection URL
        csv_path: Path to the CSV file containing project data
    
    Returns:
        Tuple of (inserted_count, skipped_count)
    """
    # Create temporary async engine using connection helper
    engine = create_temp_async_engine(database_url, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    inserted_count = 0
    skipped_count = 0
    
    print("=" * 70)
    print("Reading CSV file and inserting data into projects table...")
    print(f"CSV Path: {csv_path}")
    print("=" * 70)
    
    # Count total rows first
    with open(csv_path, 'r', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        total_rows = sum(1 for _ in reader)
    
    print(f"Total rows in CSV: {total_rows}")
    print()
    
    try:
        async with AsyncSessionLocal() as session:
            with open(csv_path, 'r', encoding='utf-8') as csv_file:
                reader = csv.DictReader(csv_file)
                
                for row_num, row in enumerate(reader, start=1):
                    # Prepare data dictionary
                    data = {}
                    for csv_col, db_col in COLUMN_MAPPING.items():
                        value = row.get(csv_col, '')
                        if value:
                            value = value.strip()
                        else:
                            value = ''
                        
                        ##> Preprocessing steps
                        if db_col == 'completion_status':
                            value = clean_completion_status(value)
                        
                        # Convert value to appropriate type
                        data[db_col] = convert_value(value, db_col)
                    
                    # Validate row before inserting
                    if not is_valid_row(data):
                        print(f"Skipping row {row_num}: Missing required fields or invalid completion status")
                        skipped_count += 1
                        continue
                    
                    # Create new project instance
                    project = Project(**data)
                    session.add(project)
                    inserted_count += 1
                    
                    if inserted_count % 100 == 0:
                        print(f"Inserted {inserted_count} records...")
                        await session.flush()  # Flush every 100 records
            
            # Commit all changes
            await session.commit()
            print(f"\n✓ Successfully inserted {inserted_count} records.")
            if skipped_count > 0:
                print(f"⚠ Skipped {skipped_count} records (duplicates, missing fields, or errors).")
    
    except Exception as e:
        print(f"\n❌ Error during data insertion: {str(e)}")
        raise
    finally:
        await engine.dispose()
    
    print("=" * 70)
    
    return inserted_count, skipped_count


##?======================================================================================


if __name__ == "__main__":
    # Run data insertion
    asyncio.run(insert_projects_data(settings.database_url, settings.csv_path))

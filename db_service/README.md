# Database Service

## What This Service Does

This service manages the database for the Proplens application. It connects to PostgreSQL, creates tables, and handles data operations. It uses SQLAlchemy ORM for database interactions with async support.

## Structure

The service is divided into two main modules:

1. **client/** - Database connection and models
2. **service/** - Database setup and data seeding

## Components

### client/

**dbmodels.py**
- Defines database tables as SQLAlchemy models
- Contains four tables:
  - `Project` - Real estate project listings
  - `Lead` - Customer leads and preferences
  - `Booking` - Property bookings linking leads to projects
  - `History` - Conversation/chat history
- Sets up relationships between tables and indexes for faster queries

**postgres_connection.py**
- Manages database connections
- Creates connection pool for efficient database access
- Provides `get_db()` function for FastAPI dependency injection
- Handles connection initialization and cleanup

### service/

**create_tables.py**
- Creates all database tables from the models
- Can drop and recreate tables if needed (use with caution)

**insert_data_projects.py**
- Reads project data from CSV file
- Validates and inserts data into the projects table
- Skips invalid or duplicate records

### Root Files

**config.py**
- Loads configuration from environment variables
- Manages database URL and CSV file paths
- Handles settings like `DATABASE_URL`, `RECREATE_DB`, etc.

**run_make_db.py**
- Script to create database tables
- Run this first to set up the database schema

**run_seed_db.py**
- Script to populate database with sample project data
- Run this after creating tables to add initial data

## How to Run

### 1. Install Dependencies

```bash
pip install sqlalchemy asyncpg psycopg2-binary python-dotenv pydantic fastapi
```

### 2. Set Up Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://username:password@host:port/database
RECREATE_DB=false
```

Example:
```env
DATABASE_URL=postgresql://myuser:mypassword@localhost:5432/proplens_db
RECREATE_DB=false
```

### 3. Create Database Tables

```bash
cd db_service
python run_make_db.py
```

This creates all tables (projects, leads, bookings, history) with proper indexes and relationships.

### 4. Seed Database with Data (Optional)

```bash
python run_seed_db.py
```

This reads `service/ProplensData.csv` and inserts project data into the database.

### 5. Use in Your Application

Initialize the database connection in your FastAPI app:

```python
from fastapi import FastAPI
from db_service.client.postgres_connection import init_psql_db_from_url, close_psql_db
from db_service.config import settings


async def lifespan(app: FastAPI):
    # In startup
    await init_psql_db_from_url(settings.database_url)

    yield

    # In shutdown
    await close_psql_db()

```

Use database sessions in your routes:

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db_service.client.postgres_connection import get_db
from db_service.client.dbmodels import Project

@app.get("/projects")
async def get_projects(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    stmt = select(Project).limit(10)
    result = await db.execute(stmt)
    return result.scalars().all()
```

## Important Notes

- Set `RECREATE_DB=true` only if you want to drop all existing tables (this deletes all data)
- Make sure PostgreSQL is running and accessible before running scripts
- The CSV file path is configured in `config.py` and defaults to `service/ProplensData.csv`

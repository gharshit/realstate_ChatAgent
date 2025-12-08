## Database Connection
"""
PostgreSQL Database Connection for FastAPI App.

This module provides PostgreSQL database connectivity using SQLAlchemy 2.0+
with asyncpg for high-performance asynchronous operations.

It leverages the existing postgres_connection.py from db_service for core functionality,
but provides a simplified interface compatible with the existing app architecture.
"""

import re
from typing import Optional, List, Dict, Any
from fastapi import HTTPException
from sqlalchemy import text

# Import the core PostgreSQL connection functionality
from db_service.client.postgres_connection import get_db as get_db_session, close_psql_db


class DatabaseConnection:
    """
    PostgreSQL database connection class using SQLAlchemy 2.0+ with asyncpg.

    Provides a simplified interface compatible with the existing app architecture
    while leveraging the robust PostgreSQL connection management from db_service.
    """

    def __init__(self):
        """Initialize PostgreSQL database connection."""
        self.initialized = False

    def _validate_query(self, query: str) -> str:
        """
        Validate query to prevent dangerous SQL operations and return query type.

        Args:
            query: SQL query string to validate

        Returns:
            Query type: 'SELECT', 'INSERT', 'UPDATE', 'WITH', etc.

        Raises:
            HTTPException: If query contains dangerous keywords
        """
        # Define dangerous SQL keywords that are not allowed
        dangerous_keywords = [
            'DELETE', 'DROP', 'TRUNCATE', 'ALTER', 'EXEC', 'EXECUTE',
            'GRANT', 'REVOKE', 'CREATE', 'REPLACE', 'ATTACH', 'DETACH'
        ]

        # Define allowed SQL keywords
        allowed_keywords = ['SELECT', 'INSERT', 'UPDATE', 'WITH']

        # Remove comments and normalize whitespace
        cleaned_query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
        cleaned_query = re.sub(r'/\*.*?\*/', '', cleaned_query, flags=re.DOTALL)
        cleaned_query = ' '.join(cleaned_query.split()).upper()

        # Check for dangerous keywords
        for keyword in dangerous_keywords:
            # Use word boundary to match whole words only
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, cleaned_query):
                raise HTTPException(
                    status_code=403,
                    detail=f"Forbidden: Query contains dangerous operation '{keyword}'. Only SELECT, INSERT, and UPDATE operations are allowed."
                )

        # Check if query starts with an allowed keyword and return the type
        query_type = cleaned_query.strip().split()[0] if cleaned_query.strip() else ""
        if query_type not in allowed_keywords:
            raise HTTPException(
                status_code=403,
                detail=f"Forbidden: Query must start with one of: {', '.join(allowed_keywords)}. Received: {query_type}"
            )

        return query_type

    async def execute_query(
        self,
        query: str,
        params: Optional[tuple] = None,
        fetch_one: bool = False,
        fetch_all: bool = True
    ) -> Optional[List[Dict[str, Any]] | Dict[str, Any] | int]:
        """
        Execute a SQL query and return appropriate results based on query type.

        Args:
            query: SQL query string
            params: Optional tuple of parameters for parameterized queries
            fetch_one: If True, return only first row (for SELECT queries)
            fetch_all: If True, return all rows (default, for SELECT queries)

        Returns:
            - For SELECT: List of dictionaries (rows) or single dict if fetch_one=True
            - For INSERT: Last inserted row ID (int)
            - For UPDATE: Number of rows affected (int)
        """
        # Validate query and get query type
        query_type = self._validate_query(query)

        # Get database session using the async generator from postgres_connection
        async for session in get_db_session():
            try:
                # Handle parameters for SQLAlchemy
                if params:
                    # For PostgreSQL with asyncpg, convert ? to :param1, :param2, etc. (named parameters)
                    # SQLAlchemy handles named parameters better than positional $1, $2
                    param_count = query.count('?')
                    # Replace ? with :param1, :param2, etc.
                    for i in range(param_count):
                        query = query.replace('?', f':param{i+1}', 1)
                    # Create dictionary with parameter names and values
                    param_dict = {f'param{i+1}': param for i, param in enumerate(params)}
                    # Execute with named parameters
                    result = await session.execute(text(query), param_dict)
                else:
                    # No parameters, execute directly
                    result = await session.execute(text(query))

                if query_type == 'SELECT' or query_type == 'WITH':
                    # For SELECT queries, no commit needed for reads
                    if fetch_one:
                        row = result.fetchone()
                        if row:
                            # Convert Row to dict using _mapping attribute
                            return dict(row._mapping)
                        return None
                    elif fetch_all:
                        rows = result.fetchall()
                        # Convert all rows to list of dicts
                        return [dict(row._mapping) for row in rows]
                    else:
                        return None

                elif query_type == 'INSERT':
                    # For INSERT queries, commit and return row count
                    await session.commit()
                    return result.rowcount

                elif query_type == 'UPDATE':
                    # For UPDATE queries, commit and return affected rows
                    await session.commit()
                    return result.rowcount

            except Exception as e:
                await session.rollback()
                raise HTTPException(
                    status_code=500,
                    detail=f"Database query error: {str(e)}"
                )


# Global database instance (will be initialized in main.py)
db: Optional[DatabaseConnection] = None

## for agent module
def get_db() -> DatabaseConnection:
    """
    Get the global database connection instance.
    Can be used for dependency injection in FastAPI or called directly.

    Usage in FastAPI routes:
        @app.get("/projects")
        async def get_projects(db: DatabaseConnection = Depends(get_db)):
            return await db.execute_query("SELECT * FROM projects")

    Usage in tools/functions:
        db = get_db()
        result = await db.execute_query("SELECT * FROM projects")

    Returns:
        DatabaseConnection instance.

    Raises:
        RuntimeError: If database not initialized.
    """
    if db is None:
        raise RuntimeError("Database connection not initialized. Call init_db() first.")
    return db


async def init_db() -> DatabaseConnection:
    """
    Initialize the global database connection instance.
    Note: PostgreSQL connection should already be initialized via init_psql_db_from_url() in main.py

    Returns:
        DatabaseConnection instance
    """
    global db
    # Create database connection instance (PostgreSQL connection already initialized in main.py)
    db = DatabaseConnection()
    return db


async def cleanup_db() -> None:
    """Cleanup PostgreSQL database connection."""
    global db
    # Close the PostgreSQL connection
    await close_psql_db()
    db = None
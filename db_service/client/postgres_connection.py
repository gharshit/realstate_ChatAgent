"""
PostgreSQL Database Access and Connection Management.

This module provides functionality for PostgreSQL database access and connection management.
It implements a singleton pattern for connection pooling and provides methods for
initializing, accessing, and closing PostgreSQL connections.

Key Features:
    - Singleton connection management
    - Connection pooling
    - Environment-based configuration
    - Async/await support via SQLAlchemy 2.0+
    - Proper connection cleanup
"""

from typing import AsyncGenerator
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine, AsyncEngine
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Initialize these as None - they'll be set up during initialization
engine: AsyncEngine | None = None
AsyncSessionLocal: async_sessionmaker[AsyncSession] | None = None


def get_postgres_config() -> str:
    """
    Get PostgreSQL configuration URL from environment.
    
    Returns:
        str: Database connection URL
        
    Raises:
        ValueError: If DATABASE_URL is not set in environment
    """
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable is not set")
    return url


def convert_to_async_url(database_url: str) -> str:
    """
    Convert PostgreSQL URL to asyncpg URL format.
    
    Removes unsupported parameters like 'sslmode' and 'channel_binding' that asyncpg doesn't accept.
    
    Args:
        database_url: PostgreSQL connection URL
        
    Returns:
        str: Async PostgreSQL URL (postgresql+asyncpg://...) with unsupported params removed
        
    Raises:
        ValueError: If database_url format is invalid
    """
    if not (database_url.startswith("postgresql://") or database_url.startswith("postgresql+asyncpg://")):
        raise ValueError("DATABASE_URL must start with postgresql:// or postgresql+asyncpg://")
    
    # Parse URL to remove unsupported query parameters
    parsed = urlparse(database_url)
    query_params = parse_qs(parsed.query)
    
    # Remove parameters that asyncpg doesn't support
    unsupported_params = ['sslmode', 'channel_binding']
    for param in unsupported_params:
        if param in query_params:
            del query_params[param]
    
    # Reconstruct URL without unsupported parameters
    new_query = urlencode(query_params, doseq=True)
    new_parsed = parsed._replace(query=new_query)
    clean_url = urlunparse(new_parsed)
    
    # Convert to asyncpg URL format
    if database_url.startswith("postgresql://"):
        return clean_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    else:
        return clean_url


def create_temp_async_engine(
    database_url: str,
    echo: bool = False,
) -> AsyncEngine:
    """
    Create a temporary async engine for one-off operations (e.g., table creation, migrations).
    
    This is useful for scripts that need a temporary connection and will dispose of it themselves.
    For persistent connections, use init_psql_db_from_url() instead.
    
    Args:
        database_url: PostgreSQL connection URL
        echo: Whether to log SQL queries
        
    Returns:
        AsyncEngine: Temporary async engine instance
        
    Raises:
        ValueError: If database_url format is invalid
    """
    async_url = convert_to_async_url(database_url)
    return create_async_engine(
        async_url,
        echo=echo,
        pool_pre_ping=True,
    )


async def init_psql_db_from_url(
    database_url: str,
    echo: bool = False,
    pool_size: int = 5,
    max_overflow: int = 10,
    pool_timeout: int = 30,
    pool_recycle: int = 2000,
) -> None:
    """
    Initialize the PostgreSQL database connection using DATABASE_URL.

    Args:
        database_url: PostgreSQL connection URL (format: postgresql://user:password@host:port/database)
        echo: Whether to log SQL queries
        pool_size: Number of connections to keep in the pool
        max_overflow: Additional connections beyond pool_size
        pool_timeout: Maximum seconds to wait for connection
        pool_recycle: Seconds before connection recycling

    Raises:
        ValueError: If database_url format is invalid
        SQLAlchemyError: If there's an error creating the engine or session maker
        ConnectionError: If unable to connect to the database
    """
    global engine, AsyncSessionLocal

    # Convert postgresql:// to postgresql+asyncpg://
    async_url = convert_to_async_url(database_url)

    try:
        # Create async engine (SQLAlchemy 2.0+ - future=True is default)
        engine = create_async_engine(
            async_url,
            echo=echo,
            pool_pre_ping=True,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            pool_use_lifo=True,
        )

        # Create async session maker
        AsyncSessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

        # Test the connection
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("PostgreSQL database initialized successfully.")

    except SQLAlchemyError as e:
        error_msg = f"SQLAlchemy error during database initialization: {str(e)}"
        print(error_msg)
        raise SQLAlchemyError(error_msg) from e
    except Exception as e:
        error_msg = f"Failed to connect to database: {str(e)}"
        print(error_msg)
        raise ConnectionError(error_msg) from e

async def init_psql_db(
    host: str,
    port: int,
    database: str,
    user: str,
    password: str,
    echo: bool = False,
    pool_size: int = 15,
    max_overflow: int = 20,
    pool_timeout: int = 30,
    pool_recycle: int = 2000,
) -> None:
    """
    Initialize the PostgreSQL database connection with provided configuration.

    Args:
        host: Database host/IP address
        port: Database port
        database: Database name
        user: Database user
        password: Database password
        echo: Whether to log SQL queries
        pool_size: Number of connections to keep in the pool
        max_overflow: Additional connections beyond pool_size
        pool_timeout: Maximum seconds to wait for connection
        pool_recycle: Seconds before connection recycling (controls how long a connection can be idle before it is recycled)

    Raises:
        SQLAlchemyError: If there's an error creating the engine or session maker
        ConnectionError: If unable to connect to the database
    """
    global engine, AsyncSessionLocal

    # Construct database URL from parameters
    async_database_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"

    try:
        # Create async engine (SQLAlchemy 2.0+ - future=True is default)
        engine = create_async_engine(
            async_database_url,
            echo=echo,
            pool_pre_ping=True,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            pool_use_lifo=True,  # Last-in-first-out: last connection used is first returned to pool
        )

        # Create async session maker
        AsyncSessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

        # Test the connection
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("PostgreSQL database initialized successfully.")

    except SQLAlchemyError as e:
        error_msg = f"SQLAlchemy error during database initialization: {str(e)}"
        print(error_msg)
        raise SQLAlchemyError(error_msg) from e
    except Exception as e:
        error_msg = f"Failed to connect to database: {str(e)}"
        print(error_msg)
        raise ConnectionError(error_msg) from e


async def close_psql_db() -> None:
    """
    Close the PostgreSQL database connection and release resources.
    
    Handles cleanup of the engine and session maker.
    """
    global engine, AsyncSessionLocal
    if engine:
        await engine.dispose()
        print("PostgreSQL database connection closed.")
    engine = None
    AsyncSessionLocal = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get a database session for dependency injection.
    
    Automatically commits any pending transactions on success and rolls back on error.
    
    Yields:
        AsyncSession: Database session
        
    Raises:
        HTTPException: If database is not initialized
        
    Note:
        If a connection is yielded inside a request, another connection/function call
        will be blocked until the first one is closed.
    """
    if AsyncSessionLocal is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database not initialized",
        )

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            print(f"Error in database transaction: {str(e)}")
            raise


def get_async_session_local():
    """
    Get the current AsyncSessionLocal instance.

    Returns:
        async_sessionmaker: The AsyncSessionLocal instance

    Raises:
        RuntimeError: If database is not initialized
    """
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_psql_db_from_url() first.")
    return AsyncSessionLocal


async def validate_db_connection() -> bool:
    """
    Validate the database connection to ensure it is working properly.

    Returns:
        bool: True if connection is valid

    Raises:
        HTTPException: If database is not initialized
        ConnectionError: If connection validation fails
    """
    if AsyncSessionLocal is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database not initialized",
        )

    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        print("Database connection validated successfully.")
        return True
    except SQLAlchemyError as e:
        error_msg = f"Database connection validation failed: {str(e)}"
        print(error_msg)
        raise ConnectionError(error_msg) from e
    except Exception as e:
        error_msg = f"Database connection validation failed: {str(e)}"
        print(error_msg)
        raise ConnectionError(error_msg) from e

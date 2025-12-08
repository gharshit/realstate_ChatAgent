"""
Pytest configuration for tests_module.
Handles async fixtures and cleanup with connection pooling.
"""
import pytest
import pytest_asyncio
import asyncio
import os
from app.utils.db_connection import init_db, cleanup_db
from db_service.client.postgres_connection import init_psql_db_from_url, close_psql_db
from app.config import settings


@pytest_asyncio.fixture(scope="module", autouse=True)
async def setup_db():
    """
    Initialize database connection pool ONCE for all tests in the module.
    
    Benefits of connection pooling:
    - Connections are reused across tests (faster)
    - No repeated init/teardown (avoids event loop issues)
    - Matches production behavior (pool lives for app lifetime)
    """
    # Set Windows event loop policy if on Windows (before any async operations)
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        # Initialize PostgreSQL connection pool (creates engine with connection pool)
        await init_psql_db_from_url(settings.database_url)
        print("✅ PostgreSQL connection pool initialized")
        
        # Initialize app database connection wrapper
        await init_db()
        print("✅ App database connection initialized")
        
        # Verify pool is working by getting a connection
        from app.utils.db_connection import get_db
        db = get_db()
        test_result = await db.execute_query(
            query="SELECT 1 as test",
            fetch_one=True
        )
        assert test_result is not None, "Database connection test failed"
        print("✅ Database connection pool verified - ready for tests")
        
        # Yield control to tests - they will all use connections from the pool
        yield
        
    finally:
        # Cleanup: close connection pool and dispose of engine
        print("🧹 Closing database connection pool...")
        try:
            # Give any pending queries time to complete
            await asyncio.sleep(0.2)
            
            # cleanup_db() calls close_psql_db() which disposes the engine and closes all pooled connections
            await cleanup_db()
            print("✅ Database connection pool closed")
        except Exception as e:
            print(f"⚠️  Cleanup error (non-fatal): {e}")
        
        # Allow async operations to complete and connections to fully close
        # This is critical for Windows ProactorEventLoop with SSL connections
        await asyncio.sleep(0.5)
        
        # Wait for any pending tasks to complete
        try:
            loop = asyncio.get_running_loop()
            current_task = asyncio.current_task(loop)
            # Get pending tasks excluding the current one
            pending = [task for task in asyncio.all_tasks(loop) 
                      if not task.done() and task != current_task]
            if pending:
                print(f"⏳ Waiting for {len(pending)} pending tasks to complete...")
                await asyncio.gather(*pending, return_exceptions=True)
        except RuntimeError:
            # No running loop - this is okay during cleanup
            pass

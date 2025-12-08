"""
Integration tests for get_current_time tool.
These tests execute the real function without mocking.
"""
import pytest
import asyncio
from datetime import datetime
from app.chatagent.tools import get_current_time
from app.utils.helpers import get_current_timestamp


@pytest.mark.asyncio
async def test_get_current_time_returns_string():
    """Test that get_current_time returns a string."""
    result = await get_current_time.ainvoke({})
    
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_get_current_time_valid_timestamp():
    """Test that get_current_time returns a valid timestamp format."""
    result = await get_current_time.ainvoke({})
    
    assert isinstance(result, str)
    
    # Should be in format 'YYYY-MM-DD HH:MM:SS'
    try:
        # Parse the datetime string format
        parsed = datetime.strptime(result, "%Y-%m-%d %H:%M:%S")
        assert parsed is not None
        
        # Verify it's a reasonable timestamp (not too old, not in future)
        current_time = get_current_timestamp()
        time_diff = abs((parsed - current_time).total_seconds())
        # Allow 5 second difference for test execution time
        assert time_diff < 5
    except ValueError:
        pytest.fail(f"Timestamp format not recognized. Expected 'YYYY-MM-DD HH:MM:SS', got: {result}")



@pytest.mark.asyncio
async def test_get_current_time_multiple_calls():
    """Test that multiple calls return timestamps."""
    result1 = await get_current_time.ainvoke({})
    await asyncio.sleep(0.1)  # Small delay
    result2 = await get_current_time.ainvoke({})
    
    # Both should be valid datetime strings
    assert isinstance(result1, str)
    assert isinstance(result2, str)
    
    # Parse both timestamps
    timestamp1 = datetime.strptime(result1, "%Y-%m-%d %H:%M:%S")
    timestamp2 = datetime.strptime(result2, "%Y-%m-%d %H:%M:%S")
    
    # Second call should be >= first call (allowing for same second)
    assert timestamp2 >= timestamp1


@pytest.mark.asyncio
async def test_get_current_time_usable_in_sql():
    """Test that the timestamp can be used in SQL queries."""
    timestamp = await get_current_time.ainvoke({})
    
    # Should be usable as a string in SQL
    assert isinstance(timestamp, str)
    assert len(timestamp) > 0
    
    # Try to use it in a SQL-like context (just verify format)
    sql_query = f"SELECT * FROM table WHERE created_at = '{timestamp}'"
    assert timestamp in sql_query

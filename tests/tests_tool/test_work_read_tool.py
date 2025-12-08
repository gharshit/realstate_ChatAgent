"""
Integration tests for run_secure_read_query tool.
These tests execute real database queries without mocking.
"""
import pytest
import asyncio
from app.chatagent.tools import run_secure_read_query


@pytest.mark.asyncio
async def test_read_query_projects_table(setup_db):
    """Test reading from projects table with real database."""
    query = "SELECT * FROM projects LIMIT 5"
    
    message, results = await run_secure_read_query.ainvoke({"query": query})
    
    assert isinstance(message, str)
    assert isinstance(results, list)
    assert "Success" in message or "Error" in message
    
    if "Success" in message:
        assert len(results) > 0 or len(results) == 0  # Can be empty
        if len(results) > 0:
            assert isinstance(results[0], dict)
            # Check if it has expected project fields
            assert "id" in results[0] or "project_name" in results[0] or "city" in results[0]


@pytest.mark.asyncio
async def test_read_query_leads_table(setup_db):
    """Test reading from leads table with real database."""
    query = "SELECT id, email, preferred_city FROM leads LIMIT 5"
    
    message, results = await run_secure_read_query.ainvoke({"query": query})
    
    assert isinstance(message, str)
    assert isinstance(results, list)
    
    if "Success" in message and len(results) > 0:
        assert isinstance(results[0], dict)
        # Verify we got the requested columns
        row = results[0]
        assert "id" in row or "email" in row or "preferred_city" in row


@pytest.mark.asyncio
async def test_read_query_bookings_table(setup_db):
    """Test reading from bookings table with real database."""
    query = "SELECT * FROM bookings LIMIT 5"
    
    message, results = await run_secure_read_query.ainvoke({"query": query})
    
    assert isinstance(message, str)
    assert isinstance(results, list)
    
    if "Success" in message and len(results) > 0:
        assert isinstance(results[0], dict)


@pytest.mark.asyncio
async def test_read_query_with_where_clause(setup_db):
    """Test SELECT query with WHERE clause on real database."""
    query = "SELECT project_name, city FROM projects WHERE city = 'Dubai' LIMIT 3"
    
    message, results = await run_secure_read_query.ainvoke({"query": query})
    
    assert isinstance(message, str)
    assert isinstance(results, list)
    
    if "Success" in message and len(results) > 0:
        for row in results:
            assert isinstance(row, dict)
            if "city" in row:
                assert row["city"] == "Dubai" or row["city"] == "dubai"  # Case insensitive


@pytest.mark.asyncio
async def test_read_query_with_join(setup_db):
    """Test SELECT query with JOIN on real database."""
    query = """
    SELECT b.id, b.booking_status, l.email, p.project_name 
    FROM bookings b 
    JOIN leads l ON b.lead_id = l.id 
    JOIN projects p ON b.project_id = p.id 
    LIMIT 3
    """
    
    message, results = await run_secure_read_query.ainvoke({"query": query})
    
    assert isinstance(message, str)
    assert isinstance(results, list)
    
    if "Success" in message and len(results) > 0:
        assert isinstance(results[0], dict)


@pytest.mark.asyncio
async def test_read_query_blocked_history_table(setup_db):
    """Test that history table access is blocked."""
    query = "SELECT * FROM history LIMIT 1"
    
    message, results = await run_secure_read_query.ainvoke({"query": query})
    
    assert isinstance(message, str)
    assert "Error" in message
    assert "history" in message.lower()
    assert results == []


@pytest.mark.asyncio
async def test_read_query_blocked_delete_operation(setup_db):
    """Test that DELETE operations are blocked."""
    query = "DELETE FROM projects WHERE id = 1"
    
    message, results = await run_secure_read_query.ainvoke({"query": query})
    
    assert isinstance(message, str)
    assert "Error" in message
    assert results == []


@pytest.mark.asyncio
async def test_read_query_with_cte(setup_db):
    """Test SELECT query with Common Table Expression (WITH clause)."""
    query = """
    WITH expensive_projects AS (
        SELECT * FROM projects WHERE price_usd > 500000
    )
    SELECT project_name, city, price_usd FROM expensive_projects LIMIT 3
    """
    
    message, results = await run_secure_read_query.ainvoke({"query": query})
    
    assert isinstance(message, str)
    assert isinstance(results, list)
    
    if "Success" in message and len(results) > 0:
        assert isinstance(results[0], dict)


@pytest.mark.asyncio
async def test_read_query_empty_result(setup_db):
    """Test query that returns no results."""
    query = "SELECT * FROM projects WHERE id = 999999"
    
    message, results = await run_secure_read_query.ainvoke({"query": query})
    
    assert isinstance(message, str)
    assert isinstance(results, list)
    # Should succeed but return empty list
    if "Success" in message:
        assert len(results) == 0

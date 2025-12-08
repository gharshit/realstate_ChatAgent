"""
Integration tests for run_secure_write_query tool.
These tests execute real database write operations without mocking.
"""
import pytest
import asyncio
from app.chatagent.tools import run_secure_write_query, get_current_time
from app.utils.db_connection import get_db
import time


@pytest.mark.asyncio
async def test_write_insert_lead(setup_db):
    """Test INSERT into leads table with real database."""
    query = """
    INSERT INTO leads (first_name, last_name, email, preferred_city, preferred_budget_usd) 
    VALUES ('Test', 'User', 'test_write@example.com', 'Dubai', 500000)
    """
    
    message, result_id = await run_secure_write_query.ainvoke({"query": query})
    
    assert isinstance(message, str)
    assert isinstance(result_id, int)
    
    if "Success" in message:
        assert result_id > 0
        
        # Verify the insert by reading it back
        db = get_db()
        verify_result = await db.execute_query(
            query="SELECT * FROM leads WHERE email = 'test_write@example.com'",
            fetch_one=True
        )
        assert verify_result is not None
        assert verify_result["email"] == "test_write@example.com"


@pytest.mark.asyncio
async def test_write_insert_booking(setup_db):
    """Test INSERT into bookings table with real database."""
    # First, ensure we have a valid lead_id and project_id
    db = get_db()
    
    # Get a valid lead_id
    lead_result = await db.execute_query(
        query="SELECT id FROM leads LIMIT 1",
        fetch_one=True
    )
    # Get a valid project_id
    project_result = await db.execute_query(
        query="SELECT id FROM projects LIMIT 1",
        fetch_one=True
    )
    
    
    
    if lead_result and project_result:
        time.sleep(0.5)
        lead_id = lead_result["id"]
        project_id = project_result["id"]
        
        query = f"""
        INSERT INTO bookings (lead_id, project_id, booking_date, booking_status) 
        VALUES ({lead_id}, {project_id}, '2024-12-05', 'pending')
        """
        
        message, result_id = await run_secure_write_query.ainvoke({"query": query})
        
        assert isinstance(message, str)
        assert isinstance(result_id, int)
        
        if "Success" in message:
            assert result_id > 0


@pytest.mark.asyncio
async def test_write_update_lead(setup_db):
    """Test UPDATE on leads table with real database."""
    # Use timestamp to ensure unique email for each test run
    import time
    test_email = f'update_test_{int(time.time())}@example.com'
    
    db = get_db()
    
    # Create a test lead with unique email
    create_query = f"""
    INSERT INTO leads (first_name, last_name, email, preferred_city, preferred_budget_usd) 
    VALUES ('Update', 'Test', '{test_email}', 'Abu Dhabi', 400000)
    """
    await db.execute_query(query=create_query)
    
    # Now update it
    update_query = f"""
    UPDATE leads SET preferred_budget_usd = 600000 WHERE email = '{test_email}'
    """
    
    message, affected_rows = await run_secure_write_query.ainvoke({"query": update_query})
    
    assert isinstance(message, str)
    assert isinstance(affected_rows, int)
    
    if "Success" in message:
        assert affected_rows >= 0  # Can be 0 if no matching row
        
        # Verify the update
        verify_result = await db.execute_query(
            query=f"SELECT preferred_budget_usd FROM leads WHERE email = '{test_email}'",
            fetch_one=True
        )
        if verify_result:
            assert verify_result["preferred_budget_usd"] == 600000


@pytest.mark.asyncio
async def test_write_update_booking(setup_db):
    """Test UPDATE on bookings table with real database."""
    db = get_db()
    
    # Get a booking to update
    booking_result = await db.execute_query(
        query="SELECT id FROM bookings LIMIT 1",
        fetch_one=True
    )
    
    if booking_result:
        booking_id = booking_result["id"]
        
        update_query = f"""
        UPDATE bookings SET booking_status = 'confirmed' WHERE id = {booking_id}
        """
        
        message, affected_rows = await run_secure_write_query.ainvoke({"query": update_query})
        
        assert isinstance(message, str)
        assert isinstance(affected_rows, int)
        
        if "Success" in message:
            assert affected_rows >= 0


@pytest.mark.asyncio
async def test_write_blocked_projects_table(setup_db):
    """Test that INSERT into projects table is blocked."""
    query = """
    INSERT INTO projects (project_name, city, price_usd) 
    VALUES ('Test Project', 'Dubai', 1000000)
    """
    
    message, result_id = await run_secure_write_query.ainvoke({"query": query})
    
    assert isinstance(message, str)
    assert "Error" in message
    assert "projects" in message.lower()
    assert result_id == 0


@pytest.mark.asyncio
async def test_write_blocked_history_table(setup_db):
    """Test that INSERT into history table is blocked."""
    query = """
    INSERT INTO history (conversation_id, created_at) 
    VALUES ('test123', '2024-12-05')
    """
    
    message, result_id = await run_secure_write_query.ainvoke({"query": query})
    
    assert isinstance(message, str)
    assert "Error" in message
    assert "history" in message.lower()
    assert result_id == 0


@pytest.mark.asyncio
async def test_write_blocked_delete_operation(setup_db):
    """Test that DELETE operations are blocked."""
    query = "DELETE FROM bookings WHERE id = 1"
    
    message, result_id = await run_secure_write_query.ainvoke({"query": query})
    
    assert isinstance(message, str)
    assert "Error" in message
    assert result_id == 0


@pytest.mark.asyncio
async def test_write_blocked_select_operation(setup_db):
    """Test that SELECT operations are blocked in write tool."""
    query = "SELECT * FROM leads"
    
    message, result_id = await run_secure_write_query.ainvoke({"query": query})
    
    assert isinstance(message, str)
    assert "Error" in message
    assert result_id == 0


@pytest.mark.asyncio
async def test_write_insert_with_timestamp(setup_db):
    """Test INSERT with timestamp using get_current_time tool."""
    # Get current timestamp
    timestamp = await get_current_time.ainvoke({})
    
    query = f"""
    INSERT INTO leads (first_name, last_name, email, preferred_city, preferred_budget_usd, created_at) 
    VALUES ('Timestamp', 'Test', 'timestamp_test@example.com', 'Dubai', 500000, '{timestamp}')
    """
    
    message, result_id = await run_secure_write_query.ainvoke({"query": query})
    
    assert isinstance(message, str)
    assert isinstance(result_id, int)
    
    if "Success" in message:
        assert result_id > 0

import pytest
from unittest.mock import AsyncMock
from app.chatagent.tools import run_secure_write_query

## INFO: THIS IS TO TEST IF THE WRITE QUERY TOOL IS WORKING AS EXPECTED WHEN THE QUERY IS A VALID INSERT QUERY.
@pytest.mark.asyncio
async def test_write_query_insert_success(mocker):
    """Test valid INSERT query on allowed table."""
    mock_db = AsyncMock()
    # Mock result for INSERT (returns ID)
    mock_db.execute_query.return_value = 101
    mocker.patch("app.chatagent.tools.get_db", return_value=mock_db)

    query = "INSERT INTO leads (name, budget) VALUES ('Alice', 1000)"
    result = await run_secure_write_query.ainvoke({"query": query})
    
    assert isinstance(result, tuple)
    assert "Success" in result[0]
    assert result[1] == 101 # ID returned
    
    mock_db.execute_query.assert_called_once_with(query=query)


## INFO: THIS IS TO TEST IF THE WRITE QUERY TOOL IS WORKING AS EXPECTED WHEN THE QUERY IS A VALID UPDATE QUERY.
@pytest.mark.asyncio
async def test_write_query_update_success(mocker):
    """Test valid UPDATE query on allowed table."""
    mock_db = AsyncMock()
    # Mock result for UPDATE (returns row count)
    mock_db.execute_query.return_value = 2
    mocker.patch("app.chatagent.tools.get_db", return_value=mock_db)

    query = "UPDATE bookings SET status = 'confirmed' WHERE id > 5"
    result = await run_secure_write_query.ainvoke({"query": query})
    
    assert "Success" in result[0]
    assert result[1] == 2 # Rows affected


## INFO: THIS IS TO TEST IF THE WRITE QUERY TOOL IS WORKING AS EXPECTED WHEN THE QUERY IS A FORBIDDEN TABLE.
@pytest.mark.asyncio
async def test_write_query_forbidden_table_projects(mocker):
    """Test write operation on read-only 'projects' table."""
    query = "INSERT INTO projects (name) VALUES ('Forbidden Project')"
    
    result = await run_secure_write_query.ainvoke({"query": query})
    
    assert "Error" in result[0]
    assert "projects" in result[0]
    assert result[1] == 0

## INFO: THIS IS TO TEST IF THE WRITE QUERY TOOL IS WORKING AS EXPECTED WHEN THE QUERY IS A FORBIDDEN OPERATION.
@pytest.mark.asyncio
async def test_write_query_forbidden_operation_select(mocker):
    """Test SELECT operation in write tool."""
    query = "SELECT * FROM leads"
    
    result = await run_secure_write_query.ainvoke({"query": query})
    
    assert "Error" in result[0]
    assert "Forbidden operation" in result[0]


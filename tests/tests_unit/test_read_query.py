import pytest
from unittest.mock import AsyncMock
from app.chatagent.tools import run_secure_read_query


## INFO: THIS IS TO TEST IF THE READ QUERY TOOL IS WORKING AS EXPECTED.
@pytest.mark.asyncio
async def test_read_query_success(mocker):
    """Test valid SELECT query on allowed table."""
    mock_db = AsyncMock()
    # Mock result for fetch_all=True
    mock_db.execute_query.return_value = [{"id": 1, "project_name": "Sky View"}]
    mocker.patch("app.chatagent.tools.get_db", return_value=mock_db)

    query = "SELECT * FROM projects"
    # Invoke tool
    result = await run_secure_read_query.ainvoke({"query": query})
    
    # Check structure: (message, data)
    assert isinstance(result, tuple)
    assert result[0].startswith("Success")
    assert len(result[1]) == 1
    assert result[1][0]["project_name"] == "Sky View"
    
    # Verify DB call
    mock_db.execute_query.assert_called_once()
    args, kwargs = mock_db.execute_query.call_args
    assert kwargs['query'] == query
    assert kwargs['fetch_all'] is True


## INFO: THIS IS TO TEST IF THE READ QUERY TOOL IS WORKING AS EXPECTED WHEN THE QUERY CONTAINS A FORBIDDEN KEYWORD.
@pytest.mark.asyncio
async def test_read_query_forbidden_keyword(mocker):
    """Test query with forbidden keyword (DELETE)."""
    query = "DELETE FROM projects WHERE id = 1"
    
    result = await run_secure_read_query.ainvoke({"query": query})
    
    assert isinstance(result, tuple)
    assert "Error" in result[0]
    assert "Forbidden operation" in result[0]
    assert result[1] == []


## INFO: THIS IS TO TEST IF THE READ QUERY TOOL IS WORKING AS EXPECTED WHEN THE QUERY CONTAINS A FORBIDDEN TABLE.
@pytest.mark.asyncio
async def test_read_query_forbidden_table_history(mocker):
    """Test query accessing forbidden 'history' table."""
    query = "SELECT * FROM history"
    
    result = await run_secure_read_query.ainvoke({"query": query})
    
    assert "Error" in result[0]
    assert "history" in result[0]
    assert result[1] == []


## INFO: THIS IS TO TEST IF THE READ QUERY TOOL IS WORKING AS EXPECTED WHEN THE QUERY IS EMPTY.
@pytest.mark.asyncio
async def test_read_query_empty(mocker):
    """Test empty query."""
    result = await run_secure_read_query.ainvoke({"query": "   "})
    assert "Error" in result[0]


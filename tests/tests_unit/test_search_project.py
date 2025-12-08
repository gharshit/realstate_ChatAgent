import pytest
from unittest.mock import Mock
from app.chatagent.tools import search_project_info

## INFO: THIS IS TO TEST IF THE SEARCH PROJECT TOOL IS WORKING AS EXPECTED WHEN THE QUERY IS A VALID SEARCH QUERY.
@pytest.mark.asyncio
async def test_search_project_success(mocker):
    """Test web search with valid parameters."""
    mock_ddg_instance = Mock()
    mock_ddg_instance.run.return_value = (
        "Title: Luxury Apt\nSnippet: Amazing views...\nLink: http://example.com"
    )
    # Patch the class itself to return our mock instance
    mocker.patch("app.chatagent.tools.DuckDuckGoSearchResults", return_value=mock_ddg_instance)

    result = await search_project_info.ainvoke({
        "project_name": "Ocean View",
        "location": "Dubai",
        "project_description": "Waterfront",
        "project_metadata": "Dubai"
    })
    
    assert isinstance(result, tuple)
    assert result[0].startswith("Success")
    assert "Luxury Apt" in result[1]
    
    # Check if run was called with combined query
    mock_ddg_instance.run.assert_called_once()
    call_arg = mock_ddg_instance.run.call_args[0][0]
    assert "Ocean View" in call_arg
    assert "Waterfront" in call_arg
    assert "Dubai" in call_arg  # Location should be included in query


## INFO: THIS IS TO TEST IF THE SEARCH PROJECT TOOL IS WORKING AS EXPECTED WHEN THE QUERY IS A NO RESULTS SEARCH QUERY.
@pytest.mark.asyncio
async def test_search_project_no_results(mocker):
    """Test web search when no results are found."""
    mock_ddg_instance = Mock()
    mock_ddg_instance.run.return_value = [] # Or empty string depending on impl, list implied by logic `if not results`
    mocker.patch("app.chatagent.tools.DuckDuckGoSearchResults", return_value=mock_ddg_instance)

    result = await search_project_info.ainvoke({
        "project_name": "Nonexistent Place",
        "location": "Dubai"
    })
    
    assert "Warning" in result[0]
    assert result[1] == ""


## INFO: THIS IS TO TEST IF THE SEARCH PROJECT TOOL IS WORKING AS EXPECTED WHEN THE QUERY IS A ERROR SEARCH QUERY.
@pytest.mark.asyncio
async def test_search_project_error(mocker):
    """Test web search handling exceptions."""
    mock_ddg_instance = Mock()
    mock_ddg_instance.run.side_effect = Exception("API Error")
    mocker.patch("app.chatagent.tools.DuckDuckGoSearchResults", return_value=mock_ddg_instance)

    result = await search_project_info.ainvoke({
        "project_name": "Error Place",
        "location": "Dubai"
    })
    
    assert "Error" in result[0]
    assert result[1] == ""


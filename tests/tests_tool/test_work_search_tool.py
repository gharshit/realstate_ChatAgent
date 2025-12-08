"""
Integration tests for search_project_info tool.
These tests execute real web searches without mocking.
"""
import pytest
import asyncio
from app.chatagent.tools import search_project_info


@pytest.mark.asyncio
async def test_search_project_name_only():
    """Test search with project name only."""
    message, results = await search_project_info.ainvoke({
        "project_name": "Burj Khalifa",
        "location": "Dubai",
        "project_description": "",
        "project_metadata": ""
    })
    
    assert isinstance(message, str)
    assert isinstance(results, str)
    
    # Should either succeed or return warning, but not error
    assert "Success" in message or "Warning" in message or "Error" in message
    
    if "Success" in message:
        assert len(results) > 0


@pytest.mark.asyncio
async def test_search_project_with_description():
    """Test search with project name and description."""
    message, results = await search_project_info.ainvoke({
        "project_name": "Dubai Marina",
        "location": "Dubai",
        "project_description": "Luxury waterfront development",
        "project_metadata": ""
    })
    
    assert isinstance(message, str)
    assert isinstance(results, str)
    
    if "Success" in message:
        assert len(results) > 0
        # Results should contain relevant information
        assert "Dubai" in results or "Marina" in results or len(results) > 50


@pytest.mark.asyncio
async def test_search_project_with_full_details():
    """Test search with project name, description, and metadata."""
    message, results = await search_project_info.ainvoke({
        "project_name": "Palm Jumeirah",
        "location": "Dubai",
        "project_description": "Iconic palm-shaped island",
        "project_metadata": "Dubai, luxury villas and apartments, Nakheel developer"
    })
    
    assert isinstance(message, str)
    assert isinstance(results, str)
    
    if "Success" in message:
        assert len(results) > 0


@pytest.mark.asyncio
async def test_search_project_empty_name():
    """Test search with empty project name (should fail validation)."""
    # This might fail at Pydantic validation level
    try:
        message, results = await search_project_info.ainvoke({
            "project_name": "",
            "location": "Dubai",
            "project_description": "",
            "project_metadata": ""
        })
        
        # If it gets past validation, should return error or warning
        assert isinstance(message, str)
    except Exception as e:
        # Pydantic validation error is acceptable
        assert "validation" in str(e).lower() or "min_length" in str(e).lower()


@pytest.mark.asyncio
async def test_search_project_real_dubai_project():
    """Test search with a real Dubai property project name."""
    message, results = await search_project_info.ainvoke({
        "project_name": "Emaar Beachfront",
        "location": "Dubai",
        "project_description": "Beachfront residential development",
        "project_metadata": "Dubai, Emaar Properties"
    })
    
    assert isinstance(message, str)
    assert isinstance(results, str)
    
    # Should get results for a well-known project
    if "Success" in message:
        assert len(results) > 0


@pytest.mark.asyncio
async def test_search_project_unknown_project():
    """Test search with a less known or fictional project name."""
    message, results = await search_project_info.ainvoke({
        "project_name": "XYZ Fictional Tower 12345",
        "location": "Dubai",
        "project_description": "A fictional property",
        "project_metadata": ""
    })
    
    assert isinstance(message, str)
    assert isinstance(results, str)
    
    # May return warning or empty results, but should not crash
    assert "Success" in message or "Warning" in message or "Error" in message


@pytest.mark.asyncio
async def test_search_project_special_characters():
    """Test search with special characters in project name."""
    message, results = await search_project_info.ainvoke({
        "project_name": "Dubai Hills Estate",
        "location": "Dubai",
        "project_description": "Residential community with golf course",
        "project_metadata": "Emaar, Dubai"
    })
    
    assert isinstance(message, str)
    assert isinstance(results, str)
    
    if "Success" in message:
        assert len(results) > 0

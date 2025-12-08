"""
Unit tests for chat node module.
Tests iteration limit enforcement, tool vs no-tool decision logic, and state updates.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import HumanMessage
from app.chatagent.nodes import chat_node
from app.config import settings


@pytest.mark.asyncio
async def test_iteration_limit_enforcement():
    """Test that iteration limit forces response at max_iterations."""
    # Set iteration_count to max_iterations
    state = {
        "messages": [HumanMessage(content="Hello")],
        "iteration_count": settings.max_iterations - 1,  # One less than max
        "conversation_id": "test_conv_123",
        "user_message": "Hello"
    }
    
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Final response"
    
    with patch('app.chatagent.nodes.get_llm_client') as mock_get_client:
        mock_client = MagicMock()
        mock_client.get_llm.return_value = mock_llm
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        
        # Call chat_node - should use get_llm (no tools) when at limit
        result = await chat_node(state)
        
        # Verify get_llm was called (not get_llm_with_tools)
        mock_client.get_llm.assert_called_once()
        mock_client.get_llm_with_tools.assert_not_called()
        
        # Verify iteration_count was incremented
        assert result["iteration_count"] == settings.max_iterations


@pytest.mark.asyncio
async def test_tool_vs_no_tool_decision_logic():
    """Test tool vs no-tool decision logic based on iteration count."""
    # Test below iteration limit - should use tools
    state_below_limit = {
        "messages": [HumanMessage(content="Hello")],
        "iteration_count": 0,
        "conversation_id": "test_conv_123",
        "user_message": "Hello"
    }
    
    mock_llm_with_tools = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Response with tools"
    
    with patch('app.chatagent.nodes.get_llm_client') as mock_get_client:
        mock_client = MagicMock()
        mock_client.get_llm_with_tools.return_value = mock_llm_with_tools
        mock_llm_with_tools.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        
        result = await chat_node(state_below_limit)
        
        # Verify get_llm_with_tools was called (below limit)
        mock_client.get_llm_with_tools.assert_called_once()
        mock_client.get_llm.assert_not_called()
        
        # Verify iteration_count was incremented
        assert result["iteration_count"] == 1


@pytest.mark.asyncio
async def test_state_updates_correctly():
    """Test that state updates correctly after chat_node execution."""
    state = {
        "messages": [HumanMessage(content="Hello")],
        "iteration_count": 0,
        "conversation_id": "test_conv_123",
        "user_message": "Hello"
    }
    
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Updated response"
    
    with patch('app.chatagent.nodes.get_llm_client') as mock_get_client:
        mock_client = MagicMock()
        mock_client.get_llm_with_tools.return_value = mock_llm
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        
        result = await chat_node(state)
        
        # Verify state updates
        assert "messages" in result
        assert "iteration_count" in result
        assert result["iteration_count"] == 1
        assert len(result["messages"]) == 1
        assert result["messages"][0] == mock_response

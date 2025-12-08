"""
Unit tests for graph builder module.
Tests graph creation, agent invocation with Request parameter.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request
from app.chatagent.builder import (
    create_property_sales_agent_graph,
    invoke_agent
)


@pytest.mark.asyncio
async def test_graph_creation_with_checkpoint():
    """Test that graph creation uses checkpoint from request.app.state."""
    # Mock Request with app.state.checkpoint
    mock_request = MagicMock(spec=Request)
    mock_checkpoint = MagicMock()
    mock_request.app.state.checkpoint = mock_checkpoint
    
    # Mock dependencies
    with patch('app.chatagent.builder.get_llm_client') as mock_get_client:
        mock_client = MagicMock()
        mock_client.get_tools.return_value = []
        mock_get_client.return_value = mock_client
        
        # Create graph
        graph = await create_property_sales_agent_graph(mock_request)
        
        assert graph is not None
        # Verify checkpoint was accessed from request.app.state
        assert mock_request.app.state.checkpoint == mock_checkpoint


@pytest.mark.asyncio
async def test_agent_invocation_success():
    """Test successful agent invocation with mocked LLM and Request."""
    # Mock Request
    mock_request = MagicMock(spec=Request)
    mock_checkpoint = MagicMock()
    mock_request.app.state.checkpoint = mock_checkpoint
    
    # Mock LLM response
    mock_ai_message = MagicMock()
    mock_ai_message.content = "Hello! How can I help you?"
    
    with patch('app.chatagent.builder.create_property_sales_agent_graph') as mock_create_graph, \
         patch('app.chatagent.builder.create_initial_state') as mock_create_state:
        
        # Mock graph
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(return_value={
            "messages": [mock_ai_message],
            "conversation_id": "test_conv_123",
            "iteration_count": 1
        })
        mock_create_graph.return_value = mock_graph
        
        # Mock initial state
        mock_create_state.return_value = {
            "user_message": "Hello",
            "messages": [],
            "conversation_id": "test_conv_123",
            "iteration_count": 0
        }
        
        # Invoke agent
        result = await invoke_agent(
            message="Hello",
            conversation_id="test_conv_123",
            is_new_conversation=True,
            request=mock_request
        )
        
        assert result["response"] == "Hello! How can I help you?"
        assert result["conversation_id"] == "test_conv_123"
        mock_graph.ainvoke.assert_called_once()
        mock_create_graph.assert_called_once_with(mock_request)


@pytest.mark.asyncio
async def test_agent_invocation_error_handling():
    """Test agent invocation error handling."""
    # Mock Request
    mock_request = MagicMock(spec=Request)
    mock_checkpoint = MagicMock()
    mock_request.app.state.checkpoint = mock_checkpoint
    
    with patch('app.chatagent.builder.create_property_sales_agent_graph') as mock_create_graph, \
         patch('app.chatagent.builder.create_initial_state') as mock_create_state:
        
        # Mock graph that raises exception
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(side_effect=Exception("Test error"))
        mock_create_graph.return_value = mock_graph
        
        # Mock initial state
        mock_create_state.return_value = {
            "user_message": "Hello",
            "messages": [],
            "conversation_id": "test_conv_123",
            "iteration_count": 0
        }
        
        # Invoke agent - should handle error gracefully
        result = await invoke_agent(
            message="Hello",
            conversation_id="test_conv_123",
            is_new_conversation=True,
            request=mock_request
        )
        
        assert result["response"] == "I encountered a system error. Please try again."
        assert result["conversation_id"] == "test_conv_123"



"""
Unit tests for graph builder module.
Tests graph creation (singleton pattern), agent invocation, and connection string cleaning.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.chatagent.builder import (
    create_property_sales_agent_graph,
    invoke_agent,
    clean_conn_string_for_psycopg
)


@pytest.mark.asyncio
async def test_graph_creation_singleton():
    """Test that graph creation returns the same instance (singleton pattern)."""
    # Reset global graph instance
    import app.chatagent.builder as builder_module
    builder_module._compiled_graph = None
    
    # Mock dependencies
    with patch('app.chatagent.builder.get_llm_client') as mock_get_client, \
         patch('app.chatagent.builder.get_checkpoint') as mock_get_checkpoint:
        
        mock_client = MagicMock()
        mock_client.get_tools.return_value = []
        mock_get_client.return_value = mock_client
        
        mock_checkpoint = MagicMock()
        mock_get_checkpoint.return_value = mock_checkpoint
        
        # Create graph first time
        graph1 = await create_property_sales_agent_graph()
        
        # Create graph second time - should return same instance
        graph2 = await create_property_sales_agent_graph()
        
        assert graph1 is graph2
        # Verify get_checkpoint was only called once (singleton behavior)
        assert mock_get_checkpoint.call_count == 1


@pytest.mark.asyncio
async def test_agent_invocation_success():
    """Test successful agent invocation with mocked LLM."""
    # Reset global graph instance
    import app.chatagent.builder as builder_module
    builder_module._compiled_graph = None
    
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
            is_new_conversation=True
        )
        
        assert result["response"] == "Hello! How can I help you?"
        assert result["conversation_id"] == "test_conv_123"
        mock_graph.ainvoke.assert_called_once()


@pytest.mark.asyncio
async def test_agent_invocation_error_handling():
    """Test agent invocation error handling."""
    # Reset global graph instance
    import app.chatagent.builder as builder_module
    builder_module._compiled_graph = None
    
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
            is_new_conversation=True
        )
        
        assert result["response"] == "I encountered a system error. Please try again."
        assert result["conversation_id"] == "test_conv_123"


def test_clean_conn_string_for_psycopg():
    """Test connection string cleaning for psycopg compatibility."""
    # Test removing unsupported 'ssl' parameter
    url_with_ssl = "postgresql://user:pass@host:5432/db?ssl=true&sslmode=require"
    cleaned = clean_conn_string_for_psycopg(url_with_ssl)
    assert "ssl=true" not in cleaned
    assert "sslmode=require" in cleaned
    
    # Test removing 'channel_binding' parameter
    url_with_channel = "postgresql://user:pass@host:5432/db?channel_binding=prefer"
    cleaned = clean_conn_string_for_psycopg(url_with_channel)
    assert "channel_binding=prefer" not in cleaned
    
    # Test non-postgresql URL (should return as-is)
    non_pg_url = "sqlite:///test.db"
    cleaned = clean_conn_string_for_psycopg(non_pg_url)
    assert cleaned == non_pg_url
    
    # Test URL without query parameters (should add default sslmode and connect_timeout)
    simple_url = "postgresql://user:pass@host:5432/db"
    cleaned = clean_conn_string_for_psycopg(simple_url)
    assert "sslmode=require" in cleaned
    assert "connect_timeout=10" in cleaned
    assert cleaned.startswith("postgresql://user:pass@host:5432/db?")

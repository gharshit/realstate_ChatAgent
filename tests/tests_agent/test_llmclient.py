"""
Unit tests for LLM client module.
Tests LLM initialization, get_llm_client returns instance/raises error, and tool binding.
"""
import pytest
from unittest.mock import patch, MagicMock
from app.chatagent.llmclient import LLMClient, init_llm, get_llm_client, cleanup_llm


def test_llm_initialization():
    """Test LLM initialization with valid parameters."""
    with patch('app.chatagent.llmclient.ChatOpenAI') as mock_chat_openai, \
         patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key-123'}):
        
        mock_llm_instance = MagicMock()
        mock_chat_openai.return_value = mock_llm_instance
        
        client = LLMClient(
            model="gpt-4o-mini",
            temperature=0.7,
            api_key="test-key-123"
        )
        
        # Verify ChatOpenAI was called with correct parameters
        mock_chat_openai.assert_called_once()
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["model"] == "gpt-4o-mini"
        assert call_kwargs["temperature"] == 0.7
        assert call_kwargs["api_key"] == "test-key-123"
        
        # Verify tools are bound
        assert hasattr(client, 'llm_with_tools')
        assert hasattr(client, 'tools')


def test_get_llm_client_returns_instance():
    """Test get_llm_client returns instance when initialized."""
    # Clean up first
    cleanup_llm()
    
    with patch('app.chatagent.llmclient.ChatOpenAI') as mock_chat_openai, \
         patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key-123'}):
        
        mock_llm_instance = MagicMock()
        mock_chat_openai.return_value = mock_llm_instance
        
        # Initialize LLM client
        init_llm(api_key="test-key-123")
        
        # Get client instance
        client = get_llm_client()
        
        assert client is not None
        assert isinstance(client, LLMClient)
        
        # Cleanup
        cleanup_llm()


def test_get_llm_client_raises_error_if_not_initialized():
    """Test get_llm_client raises error if not initialized."""
    # Clean up first
    cleanup_llm()
    
    # Try to get client without initialization
    with pytest.raises(RuntimeError, match="LLM client not initialized"):
        get_llm_client()


def test_tool_binding_works():
    """Test that tool binding works correctly."""
    with patch('app.chatagent.llmclient.ChatOpenAI') as mock_chat_openai, \
         patch('app.chatagent.llmclient.secure_sql_tools', [MagicMock(), MagicMock()]), \
         patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key-123'}):
        
        mock_llm_instance = MagicMock()
        mock_bind_tools = MagicMock(return_value="bound_llm")
        mock_llm_instance.bind_tools = mock_bind_tools
        mock_chat_openai.return_value = mock_llm_instance
        
        client = LLMClient(api_key="test-key-123")
        
        # Verify bind_tools was called
        mock_bind_tools.assert_called_once()
        
        # Verify get_llm_with_tools returns bound LLM
        assert client.get_llm_with_tools() == "bound_llm"
        
        # Verify get_tools returns tools list
        tools = client.get_tools()
        assert len(tools) == 2

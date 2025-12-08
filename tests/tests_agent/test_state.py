"""
Unit tests for state management module.
Tests create_initial_state for new/existing conversations and state structure validation.
"""
import pytest
from unittest.mock import patch, MagicMock
from langchain_core.messages import SystemMessage, HumanMessage
from app.chatagent.state import create_initial_state, AgentChatState


def test_create_initial_state_new_conversation():
    """Test create_initial_state for new conversation (includes system message)."""
    with patch('app.chatagent.state.get_AGENT_CORE_PROMPT') as mock_get_prompt:
        mock_get_prompt.return_value = "You are a helpful assistant."
        
        state = create_initial_state(
            conversation_id="test_conv_123",
            user_message="Hello",
            is_new_conversation=True
        )
        
        # Check state structure
        assert state["conversation_id"] == "test_conv_123"
        assert state["user_message"] == "Hello"
        assert state["iteration_count"] == 0
        
        # Check messages list
        messages = state["messages"]
        assert len(messages) == 2
        assert isinstance(messages[0], SystemMessage)
        assert isinstance(messages[1], HumanMessage)
        assert messages[0].content == "You are a helpful assistant."
        assert messages[1].content == "Hello"


def test_create_initial_state_existing_conversation():
    """Test create_initial_state for existing conversation (no system message)."""
    with patch('app.chatagent.state.get_AGENT_CORE_PROMPT') as mock_get_prompt:
        mock_get_prompt.return_value = "You are a helpful assistant."
        
        state = create_initial_state(
            conversation_id="test_conv_123",
            user_message="Hello again",
            is_new_conversation=False
        )
        
        # Check state structure
        assert state["conversation_id"] == "test_conv_123"
        assert state["user_message"] == "Hello again"
        assert state["iteration_count"] == 0
        
        # Check messages list - should NOT include system message
        messages = state["messages"]
        assert len(messages) == 1
        assert isinstance(messages[0], HumanMessage)
        assert messages[0].content == "Hello again"


def test_state_structure_validation():
    """Test that state structure matches AgentChatState TypedDict."""
    with patch('app.chatagent.state.get_AGENT_CORE_PROMPT') as mock_get_prompt:
        mock_get_prompt.return_value = "Test prompt"
        
        state = create_initial_state(
            conversation_id="test_conv_123",
            user_message="Test message",
            is_new_conversation=True
        )
        
        # Verify all required fields are present
        assert "user_message" in state
        assert "messages" in state
        assert "conversation_id" in state
        assert "iteration_count" in state
        
        # Verify types
        assert isinstance(state["user_message"], str)
        assert isinstance(state["messages"], list)
        assert isinstance(state["conversation_id"], str)
        assert isinstance(state["iteration_count"], int)
        
        # Verify iteration_count starts at 0
        assert state["iteration_count"] == 0

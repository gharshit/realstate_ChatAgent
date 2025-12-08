"""
Pytest configuration for chatagent unit tests.
Provides fixtures for mocking LLM client and other dependencies.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.chatagent.llmclient import LLMClient


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client for testing."""
    mock_client = MagicMock(spec=LLMClient)
    mock_client.get_llm.return_value = MagicMock()
    mock_client.get_llm_with_tools.return_value = MagicMock()
    mock_client.get_tools.return_value = []
    return mock_client


@pytest.fixture
def mock_llm_response():
    """Create a mock LLM response message."""
    mock_message = MagicMock()
    mock_message.content = "Test response"
    return mock_message

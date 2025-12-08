"""
Pytest configuration for API endpoint tests.
Provides fixtures for FastAPI TestClient and test settings.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.utils.db_connection import get_db


@pytest.fixture(scope="module", autouse=True)
def setup_mock_db():
    """
    Automatically mock database connection for all tests.
    This prevents RuntimeError when get_db() is called in tests without auth.
    Individual tests can override this if needed.
    """
    # Create a default mock database
    mock_db_instance = MagicMock()
    mock_db_instance.execute_query = AsyncMock(return_value=[])
    
    # Store original override if it exists
    original_override = app.dependency_overrides.get(get_db)
    
    # Override get_db dependency globally
    app.dependency_overrides[get_db] = lambda: mock_db_instance
    
    yield mock_db_instance
    
    # Restore original override or remove if it was added by this fixture
    if original_override is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = original_override


@pytest.fixture(scope="module")
def test_client():
    """
    Create a TestClient instance for FastAPI app.
    Note: TestClient doesn't trigger lifespan events, so no DB/LLM initialization occurs.
    """
    client = TestClient(app)
    yield client


@pytest.fixture(scope="module")
def test_api_key():
    """Test API key matching the configured ADMIN_KEY."""
    return settings.ADMIN_KEY


@pytest.fixture(scope="module")
def invalid_api_key():
    """Invalid API key for testing."""
    return "invalid_api_key_12345"


@pytest.fixture(scope="module")
def test_jwt_secret():
    """Test JWT secret key."""
    return settings.jwt_secret_key

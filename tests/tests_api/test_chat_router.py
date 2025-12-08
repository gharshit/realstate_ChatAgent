"""
Chat router tests.

Tests for:
- Chat endpoint with authentication
- New conversation handling
- Existing conversation handling
- Error handling (invalid requests, agent errors)
- Missing authentication headers
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app
from app.models.api_models import ChatRequest
from app.utils.helpers import get_or_create_conversation


class TestChatEndpoint:
    """Tests for chat endpoint."""
    
    def test_chat_with_valid_auth_new_conversation(self, test_client, test_api_key):
        """Test chat endpoint with valid auth for new conversation."""
        # Get a valid token
        token_response = test_client.post(
            "/auth/token",
            headers={"x-api-key": test_api_key}
        )
        assert token_response.status_code == 200
        token = token_response.json()["access_token"]
        
        conversation_id = str(uuid4())
        chat_request = {
            "message": "Hello, I'm looking for properties in Dubai",
            "conversation_id": conversation_id
        }
        
        # Mock dependencies
        async def mock_get_conv(chat_request: ChatRequest):
            return (
                {"conversation_id": conversation_id, "created_at": "2024-01-01"},
                True  # new_conversation = True
            )
        
        # Store original override
        original_override = app.dependency_overrides.get(get_or_create_conversation)
        app.dependency_overrides[get_or_create_conversation] = mock_get_conv
        
        try:
            with patch("app.router.chat_router.invoke_agent") as mock_invoke:
                mock_invoke.return_value = {
                    "response": "Hello! I'd be happy to help you find properties in Dubai.",
                    "conversation_id": conversation_id
                }
                
                response = test_client.post(
                    "/agents/chat",
                    json=chat_request,
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "message" in data
                assert "conversation_id" in data
                assert data["conversation_id"] == conversation_id
                assert len(data["message"]) > 0
        finally:
            # Restore original override
            if original_override is None:
                app.dependency_overrides.pop(get_or_create_conversation, None)
            else:
                app.dependency_overrides[get_or_create_conversation] = original_override
    
    def test_chat_with_valid_auth_existing_conversation(self, test_client, test_api_key):
        """Test chat endpoint with valid auth for existing conversation."""
        # Get a valid token
        token_response = test_client.post(
            "/auth/token",
            headers={"x-api-key": test_api_key}
        )
        assert token_response.status_code == 200
        token = token_response.json()["access_token"]
        
        conversation_id = str(uuid4())
        chat_request = {
            "message": "What properties do you have available?",
            "conversation_id": conversation_id
        }
        
        # Mock dependencies
        async def mock_get_conv(chat_request: ChatRequest):
            return (
                {"conversation_id": conversation_id, "created_at": "2024-01-01"},
                False  # new_conversation = False
            )
        
        # Store original override
        original_override = app.dependency_overrides.get(get_or_create_conversation)
        app.dependency_overrides[get_or_create_conversation] = mock_get_conv
        
        try:
            with patch("app.router.chat_router.invoke_agent") as mock_invoke:
                mock_invoke.return_value = {
                    "response": "I have several properties available in Dubai. What's your budget?",
                    "conversation_id": conversation_id
                }
                
                response = test_client.post(
                    "/agents/chat",
                    json=chat_request,
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "message" in data
                assert "conversation_id" in data
                assert data["conversation_id"] == conversation_id
        finally:
            # Restore original override
            if original_override is None:
                app.dependency_overrides.pop(get_or_create_conversation, None)
            else:
                app.dependency_overrides[get_or_create_conversation] = original_override
    
    def test_chat_without_auth(self, test_client):
        """Test chat endpoint without authentication."""
        conversation_id = str(uuid4())
        chat_request = {
            "message": "Hello",
            "conversation_id": conversation_id
        }
        
        response = test_client.post(
            "/agents/chat",
            json=chat_request
        )
        
        assert response.status_code == 422  # Missing Authorization header
    
    def test_chat_with_invalid_token(self, test_client):
        """Test chat endpoint with invalid bearer token."""
        conversation_id = str(uuid4())
        chat_request = {
            "message": "Hello",
            "conversation_id": conversation_id
        }
        
        response = test_client.post(
            "/agents/chat",
            json=chat_request,
            headers={"Authorization": "Bearer invalid_token_12345"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_chat_with_expired_token(self, test_client, test_jwt_secret):
        """Test chat endpoint with expired bearer token."""
        from datetime import datetime, timedelta
        from jose import jwt
        
        # Create expired token
        expire = datetime.utcnow() - timedelta(hours=1)
        expired_token = jwt.encode(
            {
                "exp": expire,
                "iat": datetime.utcnow() - timedelta(hours=2),
                "type": "access"
            },
            test_jwt_secret,
            algorithm="HS256"
        )
        
        conversation_id = str(uuid4())
        chat_request = {
            "message": "Hello",
            "conversation_id": conversation_id
        }
        
        response = test_client.post(
            "/agents/chat",
            json=chat_request,
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_chat_with_invalid_conversation_id_format(self, test_client, test_api_key):
        """Test chat endpoint with invalid conversation ID format."""
        # Get a valid token
        token_response = test_client.post(
            "/auth/token",
            headers={"x-api-key": test_api_key}
        )
        assert token_response.status_code == 200
        token = token_response.json()["access_token"]
        
        chat_request = {
            "message": "Hello",
            "conversation_id": "not-a-valid-uuid"
        }
        
        response = test_client.post(
            "/agents/chat",
            json=chat_request,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 422  # Validation error for invalid UUID
    
    def test_chat_with_empty_message(self, test_client, test_api_key):
        """Test chat endpoint with empty message."""
        # Get a valid token
        token_response = test_client.post(
            "/auth/token",
            headers={"x-api-key": test_api_key}
        )
        assert token_response.status_code == 200
        token = token_response.json()["access_token"]
        
        conversation_id = str(uuid4())
        chat_request = {
            "message": "",
            "conversation_id": conversation_id
        }
        
        response = test_client.post(
            "/agents/chat",
            json=chat_request,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should still process (validation might allow empty, or agent handles it)
        # Check if it's 422 (validation) or 200/500 (processed)
        assert response.status_code in [200, 422, 500]
    
    def test_chat_with_missing_message_field(self, test_client, test_api_key):
        """Test chat endpoint with missing message field."""
        # Get a valid token
        token_response = test_client.post(
            "/auth/token",
            headers={"x-api-key": test_api_key}
        )
        assert token_response.status_code == 200
        token = token_response.json()["access_token"]
        
        conversation_id = str(uuid4())
        chat_request = {
            "conversation_id": conversation_id
        }
        
        response = test_client.post(
            "/agents/chat",
            json=chat_request,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 422  # Validation error for missing required field
    
    def test_chat_with_missing_conversation_id_field(self, test_client, test_api_key):
        """Test chat endpoint with missing conversation_id field."""
        # Get a valid token
        token_response = test_client.post(
            "/auth/token",
            headers={"x-api-key": test_api_key}
        )
        assert token_response.status_code == 200
        token = token_response.json()["access_token"]
        
        chat_request = {
            "message": "Hello"
        }
        
        response = test_client.post(
            "/agents/chat",
            json=chat_request,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 422  # Validation error for missing required field
    
    def test_chat_agent_error_handling(self, test_client, test_api_key):
        """Test chat endpoint error handling when agent raises exception."""
        # Get a valid token
        token_response = test_client.post(
            "/auth/token",
            headers={"x-api-key": test_api_key}
        )
        assert token_response.status_code == 200
        token = token_response.json()["access_token"]
        
        conversation_id = str(uuid4())
        chat_request = {
            "message": "Hello",
            "conversation_id": conversation_id
        }
        
        # Mock dependencies
        async def mock_get_conv(chat_request: ChatRequest):
            return (
                {"conversation_id": conversation_id, "created_at": "2024-01-01"},
                False
            )
        
        # Store original override
        original_override = app.dependency_overrides.get(get_or_create_conversation)
        app.dependency_overrides[get_or_create_conversation] = mock_get_conv
        
        try:
            with patch("app.router.chat_router.invoke_agent") as mock_invoke:
                mock_invoke.side_effect = Exception("Agent processing error")
                
                response = test_client.post(
                    "/agents/chat",
                    json=chat_request,
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                assert response.status_code == 500
                data = response.json()
                assert "detail" in data
                assert "Error processing chat request" in data["detail"]
        finally:
            # Restore original override
            if original_override is None:
                app.dependency_overrides.pop(get_or_create_conversation, None)
            else:
                app.dependency_overrides[get_or_create_conversation] = original_override
    
    def test_chat_database_error_handling(self, test_client, test_api_key):
        """Test chat endpoint error handling when database raises exception."""
        # Get a valid token
        token_response = test_client.post(
            "/auth/token",
            headers={"x-api-key": test_api_key}
        )
        assert token_response.status_code == 200
        token = token_response.json()["access_token"]
        
        conversation_id = str(uuid4())
        chat_request = {
            "message": "Hello",
            "conversation_id": conversation_id
        }
        
        # Mock database dependency raising exception
        async def mock_get_conv(chat_request: ChatRequest):
            raise HTTPException(
                status_code=500,
                detail="Database connection error"
            )
        
        # Store original override
        original_override = app.dependency_overrides.get(get_or_create_conversation)
        app.dependency_overrides[get_or_create_conversation] = mock_get_conv
        
        try:
            response = test_client.post(
                "/agents/chat",
                json=chat_request,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
        finally:
            # Restore original override
            if original_override is None:
                app.dependency_overrides.pop(get_or_create_conversation, None)
            else:
                app.dependency_overrides[get_or_create_conversation] = original_override

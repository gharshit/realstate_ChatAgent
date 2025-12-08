"""
Conversation router tests.

Tests for:
- List conversations endpoint
- Get conversation history endpoint
- 404 handling for non-existent conversations
- Authentication required for all endpoints
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app
from app.utils.db_connection import get_db


class TestListConversations:
    """Tests for list conversations endpoint."""
    
    def test_list_conversations_with_valid_auth(self, test_client, test_api_key):
        """Test list conversations endpoint with valid authentication."""
        # Get a valid token
        token_response = test_client.post(
            "/auth/token",
            headers={"x-api-key": test_api_key}
        )
        assert token_response.status_code == 200
        token = token_response.json()["access_token"]
        
        # Mock database response
        mock_conversations = [
            {"conversation_id": str(uuid4()), "created_at": datetime.now()},
            {"conversation_id": str(uuid4()), "created_at": datetime.now()},
        ]
        
        mock_db = MagicMock()
        mock_db.execute_query = AsyncMock(return_value=mock_conversations)
        
        # Store original override
        original_override = app.dependency_overrides.get(get_db)
        app.dependency_overrides[get_db] = lambda: mock_db
        
        try:
            response = test_client.get(
                "/conversations/",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "conversations" in data
            assert isinstance(data["conversations"], list)
            assert len(data["conversations"]) == 2
        finally:
            # Restore original override
            if original_override is None:
                app.dependency_overrides.pop(get_db, None)
            else:
                app.dependency_overrides[get_db] = original_override
    
    def test_list_conversations_empty_list(self, test_client, test_api_key):
        """Test list conversations endpoint with no conversations."""
        # Get a valid token
        token_response = test_client.post(
            "/auth/token",
            headers={"x-api-key": test_api_key}
        )
        assert token_response.status_code == 200
        token = token_response.json()["access_token"]
        
        # Mock empty database response
        mock_db = MagicMock()
        mock_db.execute_query = AsyncMock(return_value=[])
        
        # Store original override
        original_override = app.dependency_overrides.get(get_db)
        app.dependency_overrides[get_db] = lambda: mock_db
        
        try:
            response = test_client.get(
                "/conversations/",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "conversations" in data
            assert isinstance(data["conversations"], list)
            assert len(data["conversations"]) == 0
        finally:
            # Restore original override
            if original_override is None:
                app.dependency_overrides.pop(get_db, None)
            else:
                app.dependency_overrides[get_db] = original_override
    
    def test_list_conversations_without_auth(self, test_client):
        """Test list conversations endpoint without authentication."""
        response = test_client.get("/conversations/")
        
        assert response.status_code == 422  # Missing Authorization header
    
    def test_list_conversations_with_invalid_token(self, test_client):
        """Test list conversations endpoint with invalid token."""
        response = test_client.get(
            "/conversations/",
            headers={"Authorization": "Bearer invalid_token_12345"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_list_conversations_database_error(self, test_client, test_api_key):
        """Test list conversations endpoint with database error."""
        # Get a valid token
        token_response = test_client.post(
            "/auth/token",
            headers={"x-api-key": test_api_key}
        )
        assert token_response.status_code == 200
        token = token_response.json()["access_token"]
        
        # Mock database error
        mock_db = MagicMock()
        mock_db.execute_query = AsyncMock(side_effect=Exception("Database connection error"))
        
        # Store original override
        original_override = app.dependency_overrides.get(get_db)
        app.dependency_overrides[get_db] = lambda: mock_db
        
        try:
            response = test_client.get(
                "/conversations/",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Error retrieving conversations" in data["detail"]
        finally:
            # Restore original override
            if original_override is None:
                app.dependency_overrides.pop(get_db, None)
            else:
                app.dependency_overrides[get_db] = original_override


class TestGetConversationHistory:
    """Tests for get conversation history endpoint."""
    
    def test_get_history_with_valid_auth_existing_conversation(self, test_client, test_api_key):
        """Test get history endpoint with valid auth for existing conversation."""
        # Get a valid token
        token_response = test_client.post(
            "/auth/token",
            headers={"x-api-key": test_api_key}
        )
        assert token_response.status_code == 200
        token = token_response.json()["access_token"]
        
        conversation_id = str(uuid4())
        
        # Mock database and checkpoint dependencies
        mock_db = MagicMock()
        mock_db.execute_query = AsyncMock(return_value={"conversation_id": conversation_id})
        
        # Store original override
        original_override = app.dependency_overrides.get(get_db)
        app.dependency_overrides[get_db] = lambda: mock_db
        
        try:
            with patch("app.router.convo_router.create_property_sales_agent_graph") as mock_create_graph, \
                 patch("app.router.convo_router.extract_messages_from_checkpoint_state") as mock_extract:
                
                # Mock graph state
                mock_state = MagicMock()
                mock_state.values = {"messages": []}
                mock_graph = MagicMock()
                mock_graph.aget_state = AsyncMock(return_value=mock_state)
                mock_create_graph.return_value = mock_graph
                
                # Mock message extraction
                from app.models.api_models import ChatMessage
                mock_messages = [
                    ChatMessage(message_id=1, role="user", content="Hello"),
                    ChatMessage(message_id=2, role="assistant", content="Hi there!")
                ]
                mock_extract.return_value = mock_messages
                
                response = test_client.get(
                    f"/conversations/{conversation_id}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "conversation_id" in data
                assert "messages" in data
                assert data["conversation_id"] == conversation_id
                assert isinstance(data["messages"], list)
                assert len(data["messages"]) == 2
        finally:
            # Restore original override
            if original_override is None:
                app.dependency_overrides.pop(get_db, None)
            else:
                app.dependency_overrides[get_db] = original_override
    
    def test_get_history_404_not_found(self, test_client, test_api_key):
        """Test get history endpoint returns 404 for non-existent conversation."""
        # Get a valid token
        token_response = test_client.post(
            "/auth/token",
            headers={"x-api-key": test_api_key}
        )
        assert token_response.status_code == 200
        token = token_response.json()["access_token"]
        
        conversation_id = str(uuid4())
        
        # Mock database - conversation not found
        mock_db = MagicMock()
        mock_db.execute_query = AsyncMock(return_value=None)
        
        # Store original override
        original_override = app.dependency_overrides.get(get_db)
        app.dependency_overrides[get_db] = lambda: mock_db
        
        try:
            response = test_client.get(
                f"/conversations/{conversation_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 404
            data = response.json()
            assert "detail" in data
            assert conversation_id in data["detail"]
            assert "not found" in data["detail"].lower()
        finally:
            # Restore original override
            if original_override is None:
                app.dependency_overrides.pop(get_db, None)
            else:
                app.dependency_overrides[get_db] = original_override
    
    def test_get_history_without_auth(self, test_client):
        """Test get history endpoint without authentication."""
        conversation_id = str(uuid4())
        
        response = test_client.get(f"/conversations/{conversation_id}")
        
        assert response.status_code == 422  # Missing Authorization header
    
    def test_get_history_with_invalid_token(self, test_client):
        """Test get history endpoint with invalid token."""
        conversation_id = str(uuid4())
        
        response = test_client.get(
            f"/conversations/{conversation_id}",
            headers={"Authorization": "Bearer invalid_token_12345"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_get_history_empty_messages(self, test_client, test_api_key):
        """Test get history endpoint with empty message history."""
        # Get a valid token
        token_response = test_client.post(
            "/auth/token",
            headers={"x-api-key": test_api_key}
        )
        assert token_response.status_code == 200
        token = token_response.json()["access_token"]
        
        conversation_id = str(uuid4())
        
        # Mock database and checkpoint dependencies
        mock_db = MagicMock()
        mock_db.execute_query = AsyncMock(return_value={"conversation_id": conversation_id})
        
        # Store original override
        original_override = app.dependency_overrides.get(get_db)
        app.dependency_overrides[get_db] = lambda: mock_db
        
        try:
            with patch("app.router.convo_router.create_property_sales_agent_graph") as mock_create_graph, \
                 patch("app.router.convo_router.extract_messages_from_checkpoint_state") as mock_extract:
                
                # Mock graph state
                mock_state = MagicMock()
                mock_state.values = {"messages": []}
                mock_graph = MagicMock()
                mock_graph.aget_state = AsyncMock(return_value=mock_state)
                mock_create_graph.return_value = mock_graph
                
                # Mock empty message extraction
                mock_extract.return_value = []
                
                response = test_client.get(
                    f"/conversations/{conversation_id}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "conversation_id" in data
                assert "messages" in data
                assert isinstance(data["messages"], list)
                assert len(data["messages"]) == 0
        finally:
            # Restore original override
            if original_override is None:
                app.dependency_overrides.pop(get_db, None)
            else:
                app.dependency_overrides[get_db] = original_override
    
    def test_get_history_checkpoint_error_handling(self, test_client, test_api_key):
        """Test get history endpoint handles checkpoint errors gracefully."""
        # Get a valid token
        token_response = test_client.post(
            "/auth/token",
            headers={"x-api-key": test_api_key}
        )
        assert token_response.status_code == 200
        token = token_response.json()["access_token"]
        
        conversation_id = str(uuid4())
        
        # Mock database and checkpoint dependencies
        mock_db = MagicMock()
        mock_db.execute_query = AsyncMock(return_value={"conversation_id": conversation_id})
        
        # Store original override
        original_override = app.dependency_overrides.get(get_db)
        app.dependency_overrides[get_db] = lambda: mock_db
        
        try:
            with patch("app.router.convo_router.create_property_sales_agent_graph") as mock_create_graph:
                # Mock checkpoint error
                mock_graph = MagicMock()
                mock_graph.aget_state = AsyncMock(side_effect=Exception("Checkpoint error"))
                mock_create_graph.return_value = mock_graph
                
                response = test_client.get(
                    f"/conversations/{conversation_id}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                # Should return 200 with empty messages when checkpoint fails
                assert response.status_code == 200
                data = response.json()
                assert "conversation_id" in data
                assert "messages" in data
                assert isinstance(data["messages"], list)
        finally:
            # Restore original override
            if original_override is None:
                app.dependency_overrides.pop(get_db, None)
            else:
                app.dependency_overrides[get_db] = original_override
    
    def test_get_history_database_error(self, test_client, test_api_key):
        """Test get history endpoint with database error."""
        # Get a valid token
        token_response = test_client.post(
            "/auth/token",
            headers={"x-api-key": test_api_key}
        )
        assert token_response.status_code == 200
        token = token_response.json()["access_token"]
        
        conversation_id = str(uuid4())
        
        # Mock database error
        mock_db = MagicMock()
        mock_db.execute_query = AsyncMock(side_effect=Exception("Database connection error"))
        
        # Store original override
        original_override = app.dependency_overrides.get(get_db)
        app.dependency_overrides[get_db] = lambda: mock_db
        
        try:
            response = test_client.get(
                f"/conversations/{conversation_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Error retrieving conversation history" in data["detail"]
        finally:
            # Restore original override
            if original_override is None:
                app.dependency_overrides.pop(get_db, None)
            else:
                app.dependency_overrides[get_db] = original_override
    
    def test_get_history_invalid_uuid_format(self, test_client, test_api_key):
        """Test get history endpoint with invalid UUID format."""
        # Get a valid token
        token_response = test_client.post(
            "/auth/token",
            headers={"x-api-key": test_api_key}
        )
        assert token_response.status_code == 200
        token = token_response.json()["access_token"]
        
        invalid_id = "not-a-valid-uuid"
        
        # Mock database - will return None for invalid ID
        mock_db = MagicMock()
        mock_db.execute_query = AsyncMock(return_value=None)
        
        # Store original override
        original_override = app.dependency_overrides.get(get_db)
        app.dependency_overrides[get_db] = lambda: mock_db
        
        try:
            response = test_client.get(
                f"/conversations/{invalid_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            # Should return 404 since conversation not found
            assert response.status_code == 404
            data = response.json()
            assert "detail" in data
        finally:
            # Restore original override
            if original_override is None:
                app.dependency_overrides.pop(get_db, None)
            else:
                app.dependency_overrides[get_db] = original_override

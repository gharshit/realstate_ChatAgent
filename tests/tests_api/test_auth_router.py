"""
Authentication router tests.

Tests for:
- Token generation with valid/invalid API key
- Token validation (valid, expired, invalid signature)
- Bearer token verification
- Missing authentication headers
"""
import pytest
from datetime import datetime, timedelta
from jose import jwt
from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient
from app.utils.auth import verify_bearer_token, verify_token, create_access_token
from app.config import settings


# Create a test app with a protected endpoint to test bearer token verification
test_app = FastAPI()


@test_app.get("/protected")
async def protected_endpoint(token_data: dict = Depends(verify_bearer_token)):
    """Test endpoint that requires bearer token authentication."""
    return {"message": "Access granted", "token_data": token_data}


class TestTokenGeneration:
    """Tests for token generation endpoint."""
    
    def test_generate_token_with_valid_api_key(self, test_client, test_api_key):
        """Test token generation with valid API key."""
        response = test_client.post(
            "/auth/token",
            headers={"x-api-key": test_api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0
        assert data["expires_in"] == settings.jwt_token_expiry_hours * 3600
    
    def test_generate_token_with_invalid_api_key(self, test_client, invalid_api_key):
        """Test token generation with invalid API key."""
        response = test_client.post(
            "/auth/token",
            headers={"x-api-key": invalid_api_key}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid API key" in data["detail"]
        assert "WWW-Authenticate" in response.headers
    
    def test_generate_token_with_missing_api_key(self, test_client):
        """Test token generation with missing API key header."""
        response = test_client.post("/auth/token")
        
        assert response.status_code == 422  # FastAPI validation error for missing required header
        data = response.json()
        assert "detail" in data
    
    def test_generate_token_with_empty_api_key(self, test_client):
        """Test token generation with empty API key."""
        response = test_client.post(
            "/auth/token",
            headers={"x-api-key": ""}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "API key missing" in data["detail"]


class TestTokenValidation:
    """Tests for token validation logic."""
    
    def test_verify_valid_token(self, test_api_key, test_jwt_secret):
        """Test verification of a valid token."""
        # Generate a valid token
        token = create_access_token()
        
        # Verify the token
        payload = verify_token(token)
        
        assert payload is not None
        assert "exp" in payload
        assert "iat" in payload
        assert payload["type"] == "access"
        assert isinstance(payload["exp"], (int, float))
        assert isinstance(payload["iat"], (int, float))
    
    def test_verify_expired_token(self, test_jwt_secret):
        """Test verification of an expired token."""
        # Create an expired token
        expire = datetime.utcnow() - timedelta(hours=1)
        to_encode = {
            "exp": expire,
            "iat": datetime.utcnow() - timedelta(hours=2),
            "type": "access"
        }
        expired_token = jwt.encode(
            to_encode,
            test_jwt_secret,
            algorithm="HS256"
        )
        
        # Attempt to verify expired token
        with pytest.raises(HTTPException) as exc_info:
            verify_token(expired_token)
        assert exc_info.value.status_code == 401
    
    def test_verify_token_with_invalid_signature(self, test_jwt_secret):
        """Test verification of token with invalid signature."""
        # Create a token with wrong secret key
        wrong_secret = "wrong_secret_key_12345"
        to_encode = {
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
            "type": "access"
        }
        invalid_token = jwt.encode(
            to_encode,
            wrong_secret,
            algorithm="HS256"
        )
        
        # Attempt to verify token with invalid signature
        with pytest.raises(HTTPException) as exc_info:
            verify_token(invalid_token)
        assert exc_info.value.status_code == 401
    
    def test_verify_token_with_invalid_type(self, test_jwt_secret):
        """Test verification of token with invalid type."""
        # Create a token with wrong type
        to_encode = {
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
            "type": "refresh"  # Wrong type
        }
        invalid_type_token = jwt.encode(
            to_encode,
            test_jwt_secret,
            algorithm="HS256"
        )
        
        # Attempt to verify token with invalid type
        with pytest.raises(HTTPException) as exc_info:
            verify_token(invalid_type_token)
        assert exc_info.value.status_code == 401
    
    def test_verify_malformed_token(self):
        """Test verification of malformed token."""
        malformed_token = "not.a.valid.jwt.token"
        
        # Attempt to verify malformed token
        with pytest.raises(HTTPException) as exc_info:
            verify_token(malformed_token)
        assert exc_info.value.status_code == 401


class TestBearerTokenVerification:
    """Tests for bearer token verification dependency."""
    
    @pytest.fixture
    def protected_client(self):
        """Create a test client for protected endpoints."""
        return TestClient(test_app)
    
    def test_bearer_token_verification_valid(self, protected_client, test_client, test_api_key):
        """Test bearer token verification with valid token."""
        # Get a valid token from the main app
        token_response = test_client.post(
            "/auth/token",
            headers={"x-api-key": test_api_key}
        )
        assert token_response.status_code == 200
        token = token_response.json()["access_token"]
        
        # Use token to access protected endpoint
        response = protected_client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Access granted"
        assert "token_data" in data
    
    def test_bearer_token_verification_missing_header(self, protected_client):
        """Test bearer token verification with missing Authorization header."""
        response = protected_client.get("/protected")
        
        assert response.status_code == 422  # FastAPI validation error for missing header
    
    def test_bearer_token_verification_invalid_format_no_bearer(self, protected_client):
        """Test bearer token verification with invalid format (no Bearer prefix)."""
        response = protected_client.get(
            "/protected",
            headers={"Authorization": "InvalidToken12345"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid authorization header format" in data["detail"]
        assert "WWW-Authenticate" in response.headers
    
    def test_bearer_token_verification_invalid_format_wrong_scheme(self, protected_client):
        """Test bearer token verification with wrong authorization scheme."""
        response = protected_client.get(
            "/protected",
            headers={"Authorization": "Basic dGVzdDp0ZXN0"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid authorization header format" in data["detail"]
    
    def test_bearer_token_verification_expired_token(self, protected_client, test_jwt_secret):
        """Test bearer token verification with expired token."""
        # Create an expired token
        expire = datetime.utcnow() - timedelta(hours=1)
        to_encode = {
            "exp": expire,
            "iat": datetime.utcnow() - timedelta(hours=2),
            "type": "access"
        }
        expired_token = jwt.encode(
            to_encode,
            test_jwt_secret,
            algorithm="HS256"
        )
        
        response = protected_client.get(
            "/protected",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]
    
    def test_bearer_token_verification_invalid_signature(self, protected_client, test_jwt_secret):
        """Test bearer token verification with invalid signature."""
        # Create a token with wrong secret
        wrong_secret = "wrong_secret_key_12345"
        to_encode = {
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
            "type": "access"
        }
        invalid_token = jwt.encode(
            to_encode,
            wrong_secret,
            algorithm="HS256"
        )
        
        response = protected_client.get(
            "/protected",
            headers={"Authorization": f"Bearer {invalid_token}"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]
    
    def test_bearer_token_verification_empty_token(self, protected_client):
        """Test bearer token verification with empty token."""
        response = protected_client.get(
            "/protected",
            headers={"Authorization": "Bearer "}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

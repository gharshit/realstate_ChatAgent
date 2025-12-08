"""
Authentication Router for API token generation.

This module provides REST API endpoints for authentication:
- POST /auth/token: Generate access token using API key
"""

from fastapi import APIRouter, HTTPException, status, Header
from pydantic import BaseModel, Field
from app.config import settings
from app.utils.auth import create_access_token


##> Initialize router
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


##> ============================================================================
##> AUTH MODELS
##> ============================================================================

class TokenResponse(BaseModel):
    """
    Response model for token generation.
    """
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


##> ============================================================================
##> AUTH ENDPOINTS
##> ============================================================================

@auth_router.post(
    "/token",
    response_model=TokenResponse,
    description="Generate access token using API key."
)
async def generate_token(
    x_api_key: str = Header(..., alias="x-api-key", description="API Key for authentication")
) -> TokenResponse:
    """
    Generate an access token using API key authentication.
    
    Validates the provided API key against the configured API key.
    If valid, returns a JWT access token with 1 hour validity.
    
    Args:
        x_api_key: API key provided in x-api-key header
    
    Returns:
        TokenResponse with access token and expiration info
    
    Raises:
        HTTPException: 
            - 401 if API key is missing or invalid
    """
    # Validate API key
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key missing",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    if x_api_key != settings.ADMIN_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    # Generate access token
    access_token = create_access_token()
    
    # Calculate expiration in seconds
    expires_in = settings.jwt_token_expiry_hours * 3600
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in
    )

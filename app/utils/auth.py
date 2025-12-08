"""
Authentication utilities for FastAPI application.

Provides JWT token creation and validation, and bearer token dependency
for protecting API endpoints.
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status, Header
from jose import JWTError, jwt
from app.config import settings


def create_access_token(expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        expires_delta: Optional timedelta for token expiration.
                      If None, uses default from settings (1 hour).
    
    Returns:
        str: Encoded JWT access token
    """
    if expires_delta is None:
        expires_delta = timedelta(hours=settings.jwt_token_expiry_hours)
    
    expire = datetime.utcnow() + expires_delta
    
    # Create JWT payload
    to_encode = {
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }
    
    # Encode and return token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm="HS256"
    )
    
    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    Verify and decode a JWT access token.
    
    Args:
        token: JWT token string to verify
    
    Returns:
        dict: Decoded token payload
    
    Raises:
        HTTPException: If token is invalid, expired, or malformed
    """
    try:
        # Decode token (for example, if the token is expired, it will raise an exception)
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=["HS256"]
        )
        
        # Verify token type
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        return payload
    
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )


async def verify_bearer_token(
    authorization: str = Header(..., description="Bearer token in Authorization header")
) -> dict:
    """
    FastAPI dependency to verify Bearer token from Authorization header.
    
    Usage:
        @app.get("/protected")
        async def protected_route(token_data: dict = Depends(verify_bearer_token)):
            return {"message": "Access granted"}
    
    Args:
        authorization: Authorization header value (format: "Bearer <token>")
    
    Returns:
        dict: Decoded token payload
    
    Raises:
        HTTPException: If token is missing, invalid, or expired
    """
    # Check if Authorization header is present
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Extract token from "Bearer <token>" format
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid authorization scheme")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Verify token
    return verify_token(token)

"""
Enterprise-grade security utilities.

This module provides:
- Password hashing with bcrypt
- JWT token creation and validation
- Token refresh mechanism
- Security headers utilities

Python 3.13 Compatible.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import TokenExpiredError, TokenInvalidError

logger = logging.getLogger(__name__)

# ============================================================
# Password Hashing
# ============================================================

# Password hashing context using bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Increased rounds for better security
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Uses constant-time comparison to prevent timing attacks.
    
    Args:
        plain_password: The plain text password to verify
        hashed_password: The hashed password to verify against
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.warning(f"Password verification failed: {e}")
        return False


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: The plain text password to hash
        
    Returns:
        The hashed password
    """
    return pwd_context.hash(password)


def check_password_strength(password: str) -> dict[str, Any]:
    """
    Check password strength against security requirements.
    
    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    Args:
        password: The password to check
        
    Returns:
        Dictionary with 'valid' boolean and 'errors' list
    """
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")
    
    special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    if not any(c in special_chars for c in password):
        errors.append("Password must contain at least one special character")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "strength": "strong" if len(errors) == 0 else "weak"
    }


# ============================================================
# JWT Token Management
# ============================================================

class TokenType:
    """Token type constants."""
    ACCESS = "access"
    REFRESH = "refresh"


def create_access_token(
    data: dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: The data to encode in the token (must include 'sub' for subject)
        expires_delta: Optional expiration time delta (defaults to settings)
        
    Returns:
        The encoded JWT token string
    """
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    # Add standard claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": TokenType.ACCESS
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    logger.debug(f"Access token created for subject: {data.get('sub')}")
    
    return encoded_jwt


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token.
    
    Refresh tokens have a longer expiration (7 days by default).
    
    Args:
        data: The data to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        The encoded JWT refresh token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": TokenType.REFRESH
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    logger.debug(f"Refresh token created for subject: {data.get('sub')}")
    
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and verify a JWT access token.
    
    Args:
        token: The JWT token to decode
        
    Returns:
        The decoded token payload
        
    Raises:
        TokenExpiredError: If the token has expired
        TokenInvalidError: If the token is invalid or malformed
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # Verify token type
        token_type = payload.get("type")
        if token_type != TokenType.ACCESS:
            raise TokenInvalidError("Invalid token type")
        
        # Check expiration (jose does this but we want custom error)
        exp = payload.get("exp")
        if exp:
            exp_datetime = datetime.fromtimestamp(exp, tz=timezone.utc)
            if exp_datetime < datetime.now(timezone.utc):
                raise TokenExpiredError()
        
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        raise TokenExpiredError()
    except JWTError as e:
        logger.warning(f"Token validation failed: {e}")
        raise TokenInvalidError(str(e))


def decode_refresh_token(token: str) -> dict[str, Any]:
    """
    Decode and verify a JWT refresh token.
    
    Args:
        token: The JWT refresh token to decode
        
    Returns:
        The decoded token payload
        
    Raises:
        TokenExpiredError: If the token has expired
        TokenInvalidError: If the token is invalid or malformed
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # Verify token type
        token_type = payload.get("type")
        if token_type != TokenType.REFRESH:
            raise TokenInvalidError("Invalid token type - expected refresh token")
        
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("Refresh token has expired")
        raise TokenExpiredError()
    except JWTError as e:
        logger.warning(f"Refresh token validation failed: {e}")
        raise TokenInvalidError(str(e))


def refresh_access_token(refresh_token: str) -> dict[str, str]:
    """
    Generate a new access token using a refresh token.
    
    Args:
        refresh_token: The refresh token to use
        
    Returns:
        Dictionary with new access_token and token_type
        
    Raises:
        TokenExpiredError: If the refresh token has expired
        TokenInvalidError: If the refresh token is invalid
    """
    payload = decode_refresh_token(refresh_token)
    
    # Create new access token with same subject
    subject = payload.get("sub")
    if not subject:
        raise TokenInvalidError("Refresh token missing subject")
    
    new_access_token = create_access_token(data={"sub": subject})
    
    logger.info(f"Access token refreshed for subject: {subject}")
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }


def extract_token_from_header(authorization: Optional[str]) -> Optional[str]:
    """
    Extract token from Authorization header.
    
    Args:
        authorization: The Authorization header value
        
    Returns:
        The token string or None
    """
    if not authorization:
        return None
    
    parts = authorization.split()
    
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    return parts[1]


# ============================================================
# Security Headers
# ============================================================

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
}


def get_security_headers() -> dict[str, str]:
    """
    Get security headers for HTTP responses.
    
    Returns:
        Dictionary of security headers
    """
    return SECURITY_HEADERS.copy()

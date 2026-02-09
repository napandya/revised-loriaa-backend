"""
Enterprise-grade API dependencies for Loriaa AI CRM.

This module provides:
- Authentication dependencies
- Database session dependencies
- Pagination utilities
- Rate limiting (placeholder)

Python 3.13 Compatible.
"""

from __future__ import annotations

import logging
from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, Query, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import decode_access_token, extract_token_from_header
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    UserInactiveError,
    TokenInvalidError,
    TokenExpiredError,
    NotFoundError
)
from app.models.user import User

logger = logging.getLogger(__name__)


# ============================================================
# OAuth2 Configuration
# ============================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False  # Don't auto-raise, handle manually for better errors
)


# ============================================================
# Authentication Dependencies
# ============================================================

async def get_current_user(
    token: Annotated[Optional[str], Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)]
) -> User:
    """
    Dependency to get the current authenticated user.
    
    Args:
        token: JWT token from OAuth2 bearer
        db: Database session
        
    Returns:
        The authenticated User object
        
    Raises:
        AuthenticationError: If no token provided
        TokenInvalidError: If token is invalid
        TokenExpiredError: If token has expired
        UserInactiveError: If user is inactive
        NotFoundError: If user not found
    """
    if token is None:
        raise AuthenticationError(
            message="Authentication required",
            details={"reason": "No access token provided"}
        )
    
    try:
        payload = decode_access_token(token)
    except TokenExpiredError:
        raise
    except TokenInvalidError:
        raise
    except Exception as e:
        logger.error(f"Token decode error: {e}")
        raise TokenInvalidError("Failed to decode token")
    
    email: Optional[str] = payload.get("sub")
    if email is None:
        raise TokenInvalidError("Token missing subject claim")
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        logger.warning(f"Token valid but user not found: {email}")
        raise NotFoundError(
            resource_type="User",
            message="User associated with token not found"
        )
    
    if not user.is_active:
        raise UserInactiveError(user_id=str(user.id))
    
    return user


async def get_current_user_optional(
    token: Annotated[Optional[str], Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)]
) -> Optional[User]:
    """
    Dependency to optionally get the current authenticated user.
    
    Returns None if no valid authentication is provided,
    useful for endpoints that have different behavior for
    authenticated vs anonymous users.
    
    Args:
        token: JWT token from OAuth2 bearer (optional)
        db: Database session
        
    Returns:
        The authenticated User object or None
    """
    if token is None:
        return None
    
    try:
        return await get_current_user(token, db)
    except (AuthenticationError, TokenInvalidError, TokenExpiredError):
        return None


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Dependency to ensure user is active.
    
    This is redundant with get_current_user but kept for explicit semantics.
    
    Args:
        current_user: The current user from get_current_user
        
    Returns:
        The active User object
        
    Raises:
        UserInactiveError: If user is inactive
    """
    if not current_user.is_active:
        raise UserInactiveError(user_id=str(current_user.id))
    return current_user


def require_role(required_roles: list[str]):
    """
    Dependency factory for role-based access control.
    
    Usage:
        @router.get("/admin")
        async def admin_endpoint(
            user: User = Depends(require_role(["admin"]))
        ):
            ...
    
    Args:
        required_roles: List of roles that can access the endpoint
        
    Returns:
        Dependency function that validates user role
    """
    async def role_checker(
        current_user: Annotated[User, Depends(get_current_user)]
    ) -> User:
        # Get user's role from team membership or user model
        user_role = getattr(current_user, 'role', None)
        
        if user_role is None:
            # Check team membership for role
            from app.models.team import TeamMember
            # This would need to be queried from db in real implementation
            pass
        
        if user_role not in required_roles:
            raise AuthorizationError(
                message=f"This action requires one of these roles: {', '.join(required_roles)}",
                required_permission=f"role:{required_roles}",
                resource="endpoint"
            )
        
        return current_user
    
    return role_checker


# ============================================================
# Pagination Dependencies
# ============================================================

class PaginationParams:
    """Pagination parameters with validation."""
    
    def __init__(
        self,
        skip: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
        limit: Annotated[int, Query(ge=1, le=100, description="Maximum items to return")] = 20
    ):
        self.skip = skip
        self.limit = limit
    
    @property
    def offset(self) -> int:
        """Alias for skip (database terminology)."""
        return self.skip
    
    def paginate(self, total: int) -> dict:
        """
        Generate pagination metadata.
        
        Args:
            total: Total number of items
            
        Returns:
            Pagination metadata dictionary
        """
        return {
            "total": total,
            "skip": self.skip,
            "limit": self.limit,
            "has_more": total > self.skip + self.limit,
            "page": (self.skip // self.limit) + 1,
            "pages": (total + self.limit - 1) // self.limit
        }


async def get_pagination(
    skip: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum items to return")] = 20
) -> PaginationParams:
    """
    Dependency for pagination parameters.
    
    Args:
        skip: Number of items to skip (default: 0)
        limit: Maximum items to return (default: 20, max: 100)
        
    Returns:
        PaginationParams object
    """
    return PaginationParams(skip=skip, limit=limit)


# ============================================================
# Common Filter Dependencies
# ============================================================

class CommonFilters:
    """Common filter parameters for list endpoints."""
    
    def __init__(
        self,
        search: Annotated[Optional[str], Query(
            min_length=1,
            max_length=100,
            description="Search term"
        )] = None,
        sort_by: Annotated[Optional[str], Query(
            description="Field to sort by"
        )] = None,
        sort_order: Annotated[str, Query(
            description="Sort order (asc/desc)"
        )] = "desc"
    ):
        self.search = search
        self.sort_by = sort_by
        self.sort_order = sort_order.lower()
        
        # Validate sort order
        if self.sort_order not in ("asc", "desc"):
            self.sort_order = "desc"
    
    def to_dict(self) -> dict:
        """Convert filters to dictionary."""
        return {
            "search": self.search,
            "sort_by": self.sort_by,
            "sort_order": self.sort_order
        }


async def get_common_filters(
    search: Annotated[Optional[str], Query(
        min_length=1,
        max_length=100,
        description="Search term"
    )] = None,
    sort_by: Annotated[Optional[str], Query(
        description="Field to sort by"
    )] = None,
    sort_order: Annotated[str, Query(
        description="Sort order (asc/desc)"
    )] = "desc"
) -> CommonFilters:
    """
    Dependency for common filter parameters.
    
    Returns:
        CommonFilters object
    """
    return CommonFilters(search=search, sort_by=sort_by, sort_order=sort_order)


# ============================================================
# Resource Ownership Validation
# ============================================================

def validate_resource_ownership(
    resource_user_id: UUID,
    current_user: User,
    allow_admin: bool = True
) -> bool:
    """
    Validate that a user owns a resource or is an admin.
    
    Args:
        resource_user_id: The user ID that owns the resource
        current_user: The current authenticated user
        allow_admin: Whether to allow admin users to access
        
    Returns:
        True if access is allowed
        
    Raises:
        AuthorizationError: If access is not allowed
    """
    if resource_user_id == current_user.id:
        return True
    
    if allow_admin and getattr(current_user, 'is_admin', False):
        return True
    
    raise AuthorizationError(
        message="You do not have permission to access this resource",
        resource="resource"
    )


# ============================================================
# Type Aliases for Dependency Injection
# ============================================================

# Use these for cleaner endpoint signatures
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentUserOptional = Annotated[Optional[User], Depends(get_current_user_optional)]
ActiveUser = Annotated[User, Depends(get_current_active_user)]
DbSession = Annotated[Session, Depends(get_db)]
Pagination = Annotated[PaginationParams, Depends(get_pagination)]
Filters = Annotated[CommonFilters, Depends(get_common_filters)]

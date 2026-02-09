"""
Enterprise-grade custom exceptions for Loriaa AI CRM.

This module provides a comprehensive exception hierarchy for handling
all error scenarios across the application with proper error codes,
logging integration, and HTTP response mapping.

Python 3.13 Compatible.
"""

from __future__ import annotations

import logging
import traceback
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class ErrorCode(str, Enum):
    """Standardized error codes for API responses."""
    
    # Authentication & Authorization (1xxx)
    AUTH_INVALID_CREDENTIALS = "AUTH_1001"
    AUTH_TOKEN_EXPIRED = "AUTH_1002"
    AUTH_TOKEN_INVALID = "AUTH_1003"
    AUTH_INSUFFICIENT_PERMISSIONS = "AUTH_1004"
    AUTH_USER_INACTIVE = "AUTH_1005"
    AUTH_USER_NOT_FOUND = "AUTH_1006"
    
    # Validation (2xxx)
    VALIDATION_FAILED = "VAL_2001"
    VALIDATION_MISSING_FIELD = "VAL_2002"
    VALIDATION_INVALID_FORMAT = "VAL_2003"
    VALIDATION_DUPLICATE_ENTRY = "VAL_2004"
    VALIDATION_CONSTRAINT_VIOLATION = "VAL_2005"
    
    # Resource (3xxx)
    RESOURCE_NOT_FOUND = "RES_3001"
    RESOURCE_ALREADY_EXISTS = "RES_3002"
    RESOURCE_CONFLICT = "RES_3003"
    RESOURCE_DELETED = "RES_3004"
    RESOURCE_LOCKED = "RES_3005"
    
    # Database (4xxx)
    DATABASE_ERROR = "DB_4001"
    DATABASE_CONNECTION_FAILED = "DB_4002"
    DATABASE_QUERY_FAILED = "DB_4003"
    DATABASE_TRANSACTION_FAILED = "DB_4004"
    DATABASE_INTEGRITY_ERROR = "DB_4005"
    
    # Integration (5xxx)
    INTEGRATION_ERROR = "INT_5001"
    INTEGRATION_CONNECTION_FAILED = "INT_5002"
    INTEGRATION_TIMEOUT = "INT_5003"
    INTEGRATION_INVALID_RESPONSE = "INT_5004"
    INTEGRATION_RATE_LIMITED = "INT_5005"
    INTEGRATION_AUTH_FAILED = "INT_5006"
    
    # AI Agent (6xxx)
    AGENT_ERROR = "AGT_6001"
    AGENT_EXECUTION_FAILED = "AGT_6002"
    AGENT_TIMEOUT = "AGT_6003"
    AGENT_INVALID_CONFIG = "AGT_6004"
    AGENT_QUOTA_EXCEEDED = "AGT_6005"
    
    # Voice/VAPI (7xxx)
    VOICE_ERROR = "VOI_7001"
    VOICE_CONNECTION_FAILED = "VOI_7002"
    VOICE_CALL_FAILED = "VOI_7003"
    VOICE_TRANSCRIPT_FAILED = "VOI_7004"
    VOICE_WEBHOOK_INVALID = "VOI_7005"
    
    # Rate Limiting (8xxx)
    RATE_LIMIT_EXCEEDED = "RATE_8001"
    RATE_LIMIT_API = "RATE_8002"
    RATE_LIMIT_USER = "RATE_8003"
    
    # Business Logic (9xxx)
    BUSINESS_RULE_VIOLATION = "BIZ_9001"
    BUSINESS_OPERATION_NOT_ALLOWED = "BIZ_9002"
    BUSINESS_STATE_INVALID = "BIZ_9003"
    
    # Internal (10xx)
    INTERNAL_ERROR = "INT_1001"
    INTERNAL_UNEXPECTED = "INT_1002"
    INTERNAL_CONFIG_ERROR = "INT_1003"


class LoriaaException(Exception):
    """
    Base exception class for all Loriaa application errors.
    
    Provides consistent error handling with:
    - HTTP status code mapping
    - Error codes for client identification
    - Detailed error context
    - Request correlation tracking
    - Structured logging
    
    Attributes:
        message: Human-readable error message
        error_code: Standardized error code from ErrorCode enum
        status_code: HTTP status code for the response
        details: Additional error context
        correlation_id: Unique ID for request tracing
        timestamp: When the error occurred
    """
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        cause: Optional[Exception] = None
    ) -> None:
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.correlation_id = correlation_id or str(uuid4())
        self.timestamp = datetime.now(timezone.utc)
        self.cause = cause
        
        # Log the exception
        self._log_exception()
        
        super().__init__(self.message)
    
    def _log_exception(self) -> None:
        """Log the exception with context."""
        log_data = {
            "error_code": self.error_code.value,
            "message": self.message,
            "correlation_id": self.correlation_id,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }
        
        if self.cause:
            log_data["cause"] = str(self.cause)
            log_data["traceback"] = traceback.format_exc()
        
        if self.status_code >= 500:
            logger.error(f"LoriaaException: {log_data}")
        else:
            logger.warning(f"LoriaaException: {log_data}")
    
    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for JSON response."""
        return {
            "success": False,
            "error": {
                "code": self.error_code.value,
                "message": self.message,
                "details": self.details,
                "correlation_id": self.correlation_id,
                "timestamp": self.timestamp.isoformat()
            }
        }
    
    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException."""
        return HTTPException(
            status_code=self.status_code,
            detail=self.to_dict()["error"]
        )


# ============================================================
# Authentication & Authorization Exceptions
# ============================================================

class AuthenticationError(LoriaaException):
    """Base class for authentication errors."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        error_code: ErrorCode = ErrorCode.AUTH_INVALID_CREDENTIALS,
        details: Optional[dict[str, Any]] = None
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid."""
    
    def __init__(self, message: str = "Invalid email or password") -> None:
        super().__init__(
            message=message,
            error_code=ErrorCode.AUTH_INVALID_CREDENTIALS
        )


class TokenExpiredError(AuthenticationError):
    """Raised when JWT token has expired."""
    
    def __init__(self) -> None:
        super().__init__(
            message="Access token has expired",
            error_code=ErrorCode.AUTH_TOKEN_EXPIRED,
            details={"action": "Please login again to obtain a new token"}
        )


class TokenInvalidError(AuthenticationError):
    """Raised when JWT token is malformed or invalid."""
    
    def __init__(self, reason: str = "Token validation failed") -> None:
        super().__init__(
            message="Invalid access token",
            error_code=ErrorCode.AUTH_TOKEN_INVALID,
            details={"reason": reason}
        )


class AuthorizationError(LoriaaException):
    """Raised when user lacks permission for an action."""
    
    def __init__(
        self,
        message: str = "You do not have permission to perform this action",
        required_permission: Optional[str] = None,
        resource: Optional[str] = None
    ) -> None:
        details = {}
        if required_permission:
            details["required_permission"] = required_permission
        if resource:
            details["resource"] = resource
            
        super().__init__(
            message=message,
            error_code=ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


class UserInactiveError(AuthenticationError):
    """Raised when user account is inactive."""
    
    def __init__(self, user_id: Optional[str] = None) -> None:
        details = {"action": "Please contact support to reactivate your account"}
        if user_id:
            details["user_id"] = user_id
            
        super().__init__(
            message="User account is inactive",
            error_code=ErrorCode.AUTH_USER_INACTIVE,
            details=details
        )


# ============================================================
# Validation Exceptions
# ============================================================

class ValidationError(LoriaaException):
    """Base class for validation errors."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        details: Optional[dict[str, Any]] = None
    ) -> None:
        error_details = details or {}
        if field:
            error_details["field"] = field
        if value is not None:
            error_details["invalid_value"] = str(value)[:100]  # Truncate for safety
            
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_FAILED,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=error_details
        )


class MissingFieldError(ValidationError):
    """Raised when a required field is missing."""
    
    def __init__(self, field: str) -> None:
        super().__init__(
            message=f"Required field '{field}' is missing",
            field=field
        )
        self.error_code = ErrorCode.VALIDATION_MISSING_FIELD


class InvalidFormatError(ValidationError):
    """Raised when field value has invalid format."""
    
    def __init__(self, field: str, expected_format: str, value: Any = None) -> None:
        super().__init__(
            message=f"Field '{field}' has invalid format. Expected: {expected_format}",
            field=field,
            value=value,
            details={"expected_format": expected_format}
        )
        self.error_code = ErrorCode.VALIDATION_INVALID_FORMAT


class DuplicateEntryError(ValidationError):
    """Raised when attempting to create a duplicate entry."""
    
    def __init__(self, resource_type: str, field: str, value: Any) -> None:
        super().__init__(
            message=f"{resource_type} with {field} '{value}' already exists",
            field=field,
            value=value,
            details={"resource_type": resource_type}
        )
        self.error_code = ErrorCode.VALIDATION_DUPLICATE_ENTRY
        self.status_code = status.HTTP_409_CONFLICT


# ============================================================
# Resource Exceptions
# ============================================================

class NotFoundError(LoriaaException):
    """Raised when a requested resource is not found."""
    
    def __init__(
        self,
        resource_type: str,
        resource_id: Optional[str] = None,
        message: Optional[str] = None
    ) -> None:
        default_message = f"{resource_type} not found"
        if resource_id:
            default_message = f"{resource_type} with ID '{resource_id}' not found"
            
        super().__init__(
            message=message or default_message,
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


class ResourceConflictError(LoriaaException):
    """Raised when there's a conflict with resource state."""
    
    def __init__(
        self,
        resource_type: str,
        message: str,
        current_state: Optional[str] = None,
        expected_state: Optional[str] = None
    ) -> None:
        details = {"resource_type": resource_type}
        if current_state:
            details["current_state"] = current_state
        if expected_state:
            details["expected_state"] = expected_state
            
        super().__init__(
            message=message,
            error_code=ErrorCode.RESOURCE_CONFLICT,
            status_code=status.HTTP_409_CONFLICT,
            details=details
        )


class ResourceLockedError(LoriaaException):
    """Raised when a resource is locked and cannot be modified."""
    
    def __init__(self, resource_type: str, resource_id: str, locked_by: Optional[str] = None) -> None:
        details = {"resource_type": resource_type, "resource_id": resource_id}
        if locked_by:
            details["locked_by"] = locked_by
            
        super().__init__(
            message=f"{resource_type} is currently locked and cannot be modified",
            error_code=ErrorCode.RESOURCE_LOCKED,
            status_code=status.HTTP_423_LOCKED,
            details=details
        )


# ============================================================
# Database Exceptions
# ============================================================

class DatabaseError(LoriaaException):
    """Base class for database-related errors."""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.DATABASE_ERROR,
        operation: Optional[str] = None,
        cause: Optional[Exception] = None
    ) -> None:
        details = {}
        if operation:
            details["operation"] = operation
            
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
            cause=cause
        )


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""
    
    def __init__(self, cause: Optional[Exception] = None) -> None:
        super().__init__(
            message="Failed to connect to database",
            error_code=ErrorCode.DATABASE_CONNECTION_FAILED,
            cause=cause
        )


class DatabaseQueryError(DatabaseError):
    """Raised when a database query fails."""
    
    def __init__(self, operation: str, cause: Optional[Exception] = None) -> None:
        super().__init__(
            message=f"Database query failed during {operation}",
            error_code=ErrorCode.DATABASE_QUERY_FAILED,
            operation=operation,
            cause=cause
        )


class DatabaseTransactionError(DatabaseError):
    """Raised when a database transaction fails."""
    
    def __init__(self, operation: str, cause: Optional[Exception] = None) -> None:
        super().__init__(
            message=f"Database transaction failed during {operation}",
            error_code=ErrorCode.DATABASE_TRANSACTION_FAILED,
            operation=operation,
            cause=cause
        )


# ============================================================
# Integration Exceptions
# ============================================================

class IntegrationError(LoriaaException):
    """Base class for external API integration errors."""
    
    def __init__(
        self,
        integration_name: str,
        message: str,
        error_code: ErrorCode = ErrorCode.INTEGRATION_ERROR,
        details: Optional[dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ) -> None:
        error_details = {"integration": integration_name}
        if details:
            error_details.update(details)
            
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=error_details,
            cause=cause
        )


class IntegrationConnectionError(IntegrationError):
    """Raised when connection to external service fails."""
    
    def __init__(self, integration_name: str, cause: Optional[Exception] = None) -> None:
        super().__init__(
            integration_name=integration_name,
            message=f"Failed to connect to {integration_name}",
            error_code=ErrorCode.INTEGRATION_CONNECTION_FAILED,
            cause=cause
        )


class IntegrationTimeoutError(IntegrationError):
    """Raised when external service request times out."""
    
    def __init__(self, integration_name: str, timeout_seconds: int) -> None:
        super().__init__(
            integration_name=integration_name,
            message=f"Request to {integration_name} timed out after {timeout_seconds}s",
            error_code=ErrorCode.INTEGRATION_TIMEOUT,
            details={"timeout_seconds": timeout_seconds}
        )


class IntegrationRateLimitError(IntegrationError):
    """Raised when external service rate limits are exceeded."""
    
    def __init__(self, integration_name: str, retry_after: Optional[int] = None) -> None:
        details = {}
        if retry_after:
            details["retry_after_seconds"] = retry_after
            
        super().__init__(
            integration_name=integration_name,
            message=f"{integration_name} rate limit exceeded",
            error_code=ErrorCode.INTEGRATION_RATE_LIMITED,
            details=details
        )
        self.status_code = status.HTTP_429_TOO_MANY_REQUESTS


# ============================================================
# AI Agent Exceptions
# ============================================================

class AgentError(LoriaaException):
    """Base class for AI agent errors."""
    
    def __init__(
        self,
        agent_name: str,
        message: str,
        error_code: ErrorCode = ErrorCode.AGENT_ERROR,
        details: Optional[dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ) -> None:
        error_details = {"agent": agent_name}
        if details:
            error_details.update(details)
            
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=error_details,
            cause=cause
        )


class AgentExecutionError(AgentError):
    """Raised when agent execution fails."""
    
    def __init__(self, agent_name: str, task: str, cause: Optional[Exception] = None) -> None:
        super().__init__(
            agent_name=agent_name,
            message=f"{agent_name} failed to execute task: {task}",
            error_code=ErrorCode.AGENT_EXECUTION_FAILED,
            details={"task": task},
            cause=cause
        )


class AgentQuotaExceededError(AgentError):
    """Raised when agent API quota is exceeded."""
    
    def __init__(self, agent_name: str, quota_type: str = "requests") -> None:
        super().__init__(
            agent_name=agent_name,
            message=f"{agent_name} {quota_type} quota exceeded",
            error_code=ErrorCode.AGENT_QUOTA_EXCEEDED,
            details={"quota_type": quota_type}
        )
        self.status_code = status.HTTP_429_TOO_MANY_REQUESTS


# ============================================================
# Voice/VAPI Exceptions
# ============================================================

class VoiceError(LoriaaException):
    """Base class for voice/VAPI related errors."""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.VOICE_ERROR,
        details: Optional[dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ) -> None:
        error_details = {"service": "vapi"}
        if details:
            error_details.update(details)
            
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=error_details,
            cause=cause
        )


class VoiceCallError(VoiceError):
    """Raised when voice call operations fail."""
    
    def __init__(self, operation: str, call_id: Optional[str] = None, cause: Optional[Exception] = None) -> None:
        details = {"operation": operation}
        if call_id:
            details["call_id"] = call_id
            
        super().__init__(
            message=f"Voice call {operation} failed",
            error_code=ErrorCode.VOICE_CALL_FAILED,
            details=details,
            cause=cause
        )


class VoiceWebhookError(VoiceError):
    """Raised when voice webhook validation fails."""
    
    def __init__(self, reason: str) -> None:
        super().__init__(
            message=f"Voice webhook validation failed: {reason}",
            error_code=ErrorCode.VOICE_WEBHOOK_INVALID,
            details={"reason": reason}
        )
        self.status_code = status.HTTP_400_BAD_REQUEST


# ============================================================
# Rate Limiting Exceptions
# ============================================================

class RateLimitError(LoriaaException):
    """Raised when rate limits are exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        limit_type: str = "api",
        retry_after: Optional[int] = None,
        limit: Optional[int] = None
    ) -> None:
        details = {"limit_type": limit_type}
        if retry_after:
            details["retry_after_seconds"] = retry_after
        if limit:
            details["limit"] = limit
            
        super().__init__(
            message=message,
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details
        )


# ============================================================
# Business Logic Exceptions
# ============================================================

class BusinessRuleViolationError(LoriaaException):
    """Raised when a business rule is violated."""
    
    def __init__(
        self,
        rule: str,
        message: str,
        details: Optional[dict[str, Any]] = None
    ) -> None:
        error_details = {"rule": rule}
        if details:
            error_details.update(details)
            
        super().__init__(
            message=message,
            error_code=ErrorCode.BUSINESS_RULE_VIOLATION,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=error_details
        )


class InvalidStateTransitionError(BusinessRuleViolationError):
    """Raised when an invalid state transition is attempted."""
    
    def __init__(
        self,
        resource_type: str,
        current_state: str,
        target_state: str,
        allowed_transitions: Optional[list[str]] = None
    ) -> None:
        details = {
            "resource_type": resource_type,
            "current_state": current_state,
            "target_state": target_state
        }
        if allowed_transitions:
            details["allowed_transitions"] = allowed_transitions
            
        super().__init__(
            rule="state_transition",
            message=f"Cannot transition {resource_type} from '{current_state}' to '{target_state}'",
            details=details
        )


# ============================================================
# Exception Handlers
# ============================================================

async def loriaa_exception_handler(request: Request, exc: LoriaaException) -> JSONResponse:
    """
    Global exception handler for LoriaaException.
    
    Converts LoriaaException to a standardized JSON response with proper
    HTTP status code and error details.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
        headers={"X-Correlation-ID": exc.correlation_id}
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handler for unexpected exceptions.
    
    Catches any unhandled exceptions and converts them to a standardized
    error response while logging the full details.
    """
    correlation_id = str(uuid4())
    
    logger.exception(
        f"Unhandled exception: {exc}",
        extra={
            "correlation_id": correlation_id,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": ErrorCode.INTERNAL_UNEXPECTED.value,
                "message": "An unexpected error occurred",
                "correlation_id": correlation_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        },
        headers={"X-Correlation-ID": correlation_id}
    )


def register_exception_handlers(app) -> None:
    """Register all exception handlers with the FastAPI app."""
    app.add_exception_handler(LoriaaException, loriaa_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

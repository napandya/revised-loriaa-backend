"""
Core module for Loriaa AI CRM.

This module exports:
- Configuration settings
- Exception classes
- Security utilities
- Logging configuration

Python 3.13 Compatible.
"""

from app.core.config import settings, Settings
from app.core.exceptions import (
    # Base
    LoriaaException,
    ErrorCode,
    
    # Authentication
    AuthenticationError,
    InvalidCredentialsError,
    TokenExpiredError,
    TokenInvalidError,
    AuthorizationError,
    UserInactiveError,
    
    # Validation
    ValidationError,
    MissingFieldError,
    InvalidFormatError,
    DuplicateEntryError,
    
    # Resources
    NotFoundError,
    ResourceConflictError,
    ResourceLockedError,
    
    # Database
    DatabaseError,
    DatabaseConnectionError,
    DatabaseQueryError,
    DatabaseTransactionError,
    
    # Integration
    IntegrationError,
    IntegrationConnectionError,
    IntegrationTimeoutError,
    IntegrationRateLimitError,
    
    # Agent
    AgentError,
    AgentExecutionError,
    AgentQuotaExceededError,
    
    # Voice
    VoiceError,
    VoiceCallError,
    VoiceWebhookError,
    
    # Rate Limiting
    RateLimitError,
    
    # Business Logic
    BusinessRuleViolationError,
    InvalidStateTransitionError,
    
    # Handlers
    loriaa_exception_handler,
    generic_exception_handler,
    register_exception_handlers,
)
from app.core.security import (
    verify_password,
    get_password_hash,
    check_password_strength,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    refresh_access_token,
    extract_token_from_header,
    get_security_headers,
    TokenType,
)
from app.core.logging import (
    configure_logging,
    get_logger,
    LoggerMixin,
)

__all__ = [
    # Config
    "settings",
    "Settings",
    
    # Exceptions - Base
    "LoriaaException",
    "ErrorCode",
    
    # Exceptions - Auth
    "AuthenticationError",
    "InvalidCredentialsError",
    "TokenExpiredError",
    "TokenInvalidError",
    "AuthorizationError",
    "UserInactiveError",
    
    # Exceptions - Validation
    "ValidationError",
    "MissingFieldError",
    "InvalidFormatError",
    "DuplicateEntryError",
    
    # Exceptions - Resources
    "NotFoundError",
    "ResourceConflictError",
    "ResourceLockedError",
    
    # Exceptions - Database
    "DatabaseError",
    "DatabaseConnectionError",
    "DatabaseQueryError",
    "DatabaseTransactionError",
    
    # Exceptions - Integration
    "IntegrationError",
    "IntegrationConnectionError",
    "IntegrationTimeoutError",
    "IntegrationRateLimitError",
    
    # Exceptions - Agent
    "AgentError",
    "AgentExecutionError",
    "AgentQuotaExceededError",
    
    # Exceptions - Voice
    "VoiceError",
    "VoiceCallError",
    "VoiceWebhookError",
    
    # Exceptions - Rate Limiting
    "RateLimitError",
    
    # Exceptions - Business
    "BusinessRuleViolationError",
    "InvalidStateTransitionError",
    
    # Exception Handlers
    "loriaa_exception_handler",
    "generic_exception_handler",
    "register_exception_handlers",
    
    # Security
    "verify_password",
    "get_password_hash",
    "check_password_strength",
    "create_access_token",
    "create_refresh_token",
    "decode_access_token",
    "decode_refresh_token",
    "refresh_access_token",
    "extract_token_from_header",
    "get_security_headers",
    "TokenType",
    
    # Logging
    "configure_logging",
    "get_logger",
    "LoggerMixin",
]

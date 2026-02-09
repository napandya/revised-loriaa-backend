"""
Enterprise-grade logging configuration for Loriaa AI CRM.

This module provides:
- Structured JSON logging for production
- Pretty console logging for development
- Request correlation tracking
- Log level configuration via environment

Python 3.13 Compatible.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging in production.
    
    Outputs logs in JSON format suitable for log aggregation services
    like ELK, Splunk, or CloudWatch.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in (
                'name', 'msg', 'args', 'created', 'filename', 'funcName',
                'levelname', 'levelno', 'lineno', 'module', 'msecs',
                'pathname', 'process', 'processName', 'relativeCreated',
                'stack_info', 'exc_info', 'exc_text', 'thread', 'threadName',
                'message', 'taskName'
            ):
                log_data[key] = value
        
        return json.dumps(log_data, default=str)


class PrettyFormatter(logging.Formatter):
    """
    Pretty formatter for development with colors.
    """
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        
        # Format the timestamp
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        
        # Build the log message
        message = f"{color}{timestamp} | {record.levelname:8} | {record.name} | {record.getMessage()}{self.RESET}"
        
        # Add exception info if present
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"
        
        return message


def configure_logging(
    log_level: Optional[str] = None,
    json_format: Optional[bool] = None
) -> None:
    """
    Configure application logging.
    
    Args:
        log_level: Override log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Force JSON format (True) or pretty format (False)
    """
    # Determine log level
    level_name = log_level or (
        "DEBUG" if settings.ENVIRONMENT == "development" else "INFO"
    )
    level = getattr(logging, level_name.upper(), logging.INFO)
    
    # Determine format
    use_json = json_format if json_format is not None else (
        settings.ENVIRONMENT == "production"
    )
    
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    
    # Set formatter
    if use_json:
        formatter = JSONFormatter()
    else:
        formatter = PrettyFormatter()
    
    handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]
    
    # Configure specific loggers
    _configure_library_loggers(level)
    
    # Log configuration
    logging.info(
        f"Logging configured",
        extra={
            "level": level_name,
            "format": "json" if use_json else "pretty",
            "environment": settings.ENVIRONMENT
        }
    )


def _configure_library_loggers(app_level: int) -> None:
    """
    Configure logging levels for third-party libraries.
    
    Reduces noise from chatty libraries while keeping app logs verbose.
    """
    # SQLAlchemy - only show warnings and above
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.WARNING if app_level >= logging.INFO else logging.INFO
    )
    
    # Uvicorn
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    # HTTP libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    # Passlib (password hashing)
    logging.getLogger("passlib").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the application's configuration.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured Logger instance
    """
    return logging.getLogger(name)


class LoggerMixin:
    """
    Mixin class to add logging to any class.
    
    Usage:
        class MyService(LoggerMixin):
            def do_something(self):
                self.logger.info("Doing something")
    """
    
    @property
    def logger(self) -> logging.Logger:
        if not hasattr(self, '_logger'):
            self._logger = logging.getLogger(
                f"{self.__class__.__module__}.{self.__class__.__name__}"
            )
        return self._logger


# Configure logging on module import
configure_logging()

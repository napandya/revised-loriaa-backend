"""
OpenAI Client Configuration.

Provides a configured OpenAI client with:
- Automatic retries with exponential backoff
- Rate limiting handling
- Error handling with custom exceptions
- Async support

Python 3.13 Compatible.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

from openai import OpenAI, AsyncOpenAI, APIError, RateLimitError, APIConnectionError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.core.config import settings
from app.core.exceptions import (
    IntegrationError,
    IntegrationConnectionError,
    IntegrationRateLimitError,
    IntegrationTimeoutError,
)

logger = logging.getLogger(__name__)


class OpenAIClient:
    """
    OpenAI client wrapper with enterprise features.
    
    Features:
    - Automatic retries with exponential backoff
    - Rate limit handling
    - Connection error handling
    - Configurable timeouts
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        organization: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3
    ):
        """
        Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key (defaults to settings)
            organization: OpenAI organization ID (optional)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.organization = organization
        self.timeout = timeout
        self.max_retries = max_retries
        
        if not self.api_key:
            logger.warning("OpenAI API key not configured")
        
        # Initialize sync client
        self._client: Optional[OpenAI] = None
        self._async_client: Optional[AsyncOpenAI] = None
    
    @property
    def client(self) -> OpenAI:
        """Get synchronous OpenAI client."""
        if self._client is None:
            self._client = OpenAI(
                api_key=self.api_key,
                organization=self.organization,
                timeout=self.timeout,
                max_retries=self.max_retries
            )
        return self._client
    
    @property
    def async_client(self) -> AsyncOpenAI:
        """Get asynchronous OpenAI client."""
        if self._async_client is None:
            self._async_client = AsyncOpenAI(
                api_key=self.api_key,
                organization=self.organization,
                timeout=self.timeout,
                max_retries=self.max_retries
            )
        return self._async_client
    
    def is_configured(self) -> bool:
        """Check if OpenAI is properly configured."""
        return bool(self.api_key)
    
    @retry(
        retry=retry_if_exception_type((APIConnectionError, RateLimitError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _handle_api_call(self, func, *args, **kwargs):
        """
        Execute API call with retry logic.
        
        Args:
            func: The API function to call
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            API response
            
        Raises:
            IntegrationError: On API errors
        """
        try:
            return func(*args, **kwargs)
        except RateLimitError as e:
            logger.warning(f"OpenAI rate limit hit: {e}")
            raise IntegrationRateLimitError(
                integration_name="OpenAI",
                retry_after=60
            )
        except APIConnectionError as e:
            logger.error(f"OpenAI connection error: {e}")
            raise IntegrationConnectionError(
                integration_name="OpenAI",
                cause=e
            )
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise IntegrationError(
                integration_name="OpenAI",
                message=f"OpenAI API error: {str(e)}",
                cause=e
            )


@lru_cache()
def get_openai_client() -> OpenAIClient:
    """
    Get singleton OpenAI client instance.
    
    Returns:
        Configured OpenAIClient
    """
    return OpenAIClient()

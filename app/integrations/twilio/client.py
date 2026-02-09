"""Twilio API client."""

from typing import Optional, Dict, Any, List
import httpx
from base64 import b64encode
from app.core.config import settings
from app.core.exceptions import IntegrationError


class TwilioClient:
    """Client for interacting with Twilio API."""
    
    def __init__(self):
        """Initialize Twilio client with settings."""
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.phone_number = settings.TWILIO_PHONE_NUMBER
        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}"
        
        if not self.account_sid or not self.auth_token:
            raise IntegrationError(
                message="Twilio credentials not configured",
                integration_name="twilio"
            )
        
        if not self.phone_number:
            raise IntegrationError(
                message="Twilio phone number not configured",
                integration_name="twilio"
            )
        
        # Create basic auth header
        credentials = f"{self.account_sid}:{self.auth_token}"
        encoded_credentials = b64encode(credentials.encode()).decode()
        self.headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to Twilio API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Request body data (will be form-encoded)
            params: Query parameters
            
        Returns:
            Response data as dictionary
            
        Raises:
            IntegrationError: If the request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    data=data,  # Form-encoded
                    params=params,
                    timeout=30.0
                )
                
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else str(e)
            raise IntegrationError(
                message=f"Twilio API request failed: {e.response.status_code}",
                integration_name="twilio",
                details={
                    "status_code": e.response.status_code,
                    "error": error_detail,
                    "endpoint": endpoint
                }
            )
        except httpx.RequestError as e:
            raise IntegrationError(
                message=f"Twilio API connection error: {str(e)}",
                integration_name="twilio",
                details={"endpoint": endpoint}
            )
        except Exception as e:
            raise IntegrationError(
                message=f"Unexpected error during Twilio API request: {str(e)}",
                integration_name="twilio",
                details={"endpoint": endpoint}
            )
    
    async def send_sms(
        self,
        to: str,
        body: str,
        from_number: Optional[str] = None,
        media_url: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Send an SMS message.
        
        Args:
            to: Recipient phone number (E.164 format)
            body: Message body
            from_number: Sender phone number (defaults to configured number)
            media_url: Optional list of media URLs for MMS
            
        Returns:
            Message data including SID
        """
        data = {
            "To": to,
            "Body": body,
            "From": from_number or self.phone_number
        }
        
        if media_url:
            data["MediaUrl"] = media_url
        
        return await self._request(
            method="POST",
            endpoint="/Messages.json",
            data=data
        )
    
    async def get_message(self, message_sid: str) -> Dict[str, Any]:
        """Get details of a specific message.
        
        Args:
            message_sid: Twilio message SID
            
        Returns:
            Message details
        """
        return await self._request(
            method="GET",
            endpoint=f"/Messages/{message_sid}.json"
        )
    
    async def get_message_history(
        self,
        phone: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get message history for a phone number.
        
        Args:
            phone: Phone number (E.164 format)
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of message data
        """
        params = {
            "To": phone,
            "PageSize": limit
        }
        
        response = await self._request(
            method="GET",
            endpoint="/Messages.json",
            params=params
        )
        
        return response.get("messages", [])
    
    async def get_messages_from(
        self,
        phone: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get messages sent from a phone number.
        
        Args:
            phone: Phone number (E.164 format)
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of message data
        """
        params = {
            "From": phone,
            "PageSize": limit
        }
        
        response = await self._request(
            method="GET",
            endpoint="/Messages.json",
            params=params
        )
        
        return response.get("messages", [])
    
    async def get_conversation_history(
        self,
        phone: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get full conversation history with a phone number.
        
        Args:
            phone: Phone number (E.164 format)
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of messages sorted by date (sent and received)
        """
        # Get messages sent to phone
        sent = await self.get_message_history(phone, limit // 2)
        
        # Get messages received from phone
        received = await self.get_messages_from(phone, limit // 2)
        
        # Combine and sort by date
        all_messages = sent + received
        all_messages.sort(key=lambda m: m.get("date_sent", ""), reverse=True)
        
        return all_messages[:limit]

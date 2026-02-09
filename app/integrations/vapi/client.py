"""Vapi API client for voice call management."""

from typing import Optional, Dict, Any, List
import httpx
from app.core.config import settings
from app.core.exceptions import VoiceError


class VapiClient:
    """Client for interacting with Vapi voice API."""
    
    def __init__(self):
        """Initialize Vapi client with settings."""
        self.base_url = settings.VAPI_BASE_URL
        self.api_key = settings.VAPI_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to Vapi API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters
            
        Returns:
            Response data as dictionary
            
        Raises:
            VoiceError: If the request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data,
                    params=params,
                    timeout=30.0
                )
                
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else str(e)
            raise VoiceError(
                message=f"Vapi API request failed: {e.response.status_code}",
                details={
                    "status_code": e.response.status_code,
                    "error": error_detail,
                    "endpoint": endpoint
                }
            )
        except httpx.RequestError as e:
            raise VoiceError(
                message=f"Vapi API connection error: {str(e)}",
                details={"endpoint": endpoint}
            )
        except Exception as e:
            raise VoiceError(
                message=f"Unexpected error during Vapi API request: {str(e)}",
                details={"endpoint": endpoint}
            )
    
    async def create_assistant(
        self,
        name: str,
        first_message: str,
        system_prompt: str,
        model: str = "gpt-4",
        voice_id: str = "en-US-Neural2-F",
        functions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Create a new Vapi assistant.
        
        Args:
            name: Assistant name
            first_message: Initial greeting message
            system_prompt: System prompt for assistant behavior
            model: LLM model to use
            voice_id: Voice identifier
            functions: Optional list of function definitions
            
        Returns:
            Created assistant data with assistant_id
        """
        data = {
            "name": name,
            "firstMessage": first_message,
            "model": {
                "provider": "openai",
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    }
                ]
            },
            "voice": {
                "provider": "11labs" if settings.ELEVENLABS_API_KEY else "playht",
                "voiceId": voice_id
            }
        }
        
        if functions:
            data["model"]["functions"] = functions
        
        return await self._request("POST", "/assistant", data=data)
    
    async def update_assistant(
        self,
        assistant_id: str,
        name: Optional[str] = None,
        first_message: Optional[str] = None,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        voice_id: Optional[str] = None,
        functions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Update an existing Vapi assistant.
        
        Args:
            assistant_id: Assistant ID to update
            name: New assistant name
            first_message: New initial greeting message
            system_prompt: New system prompt
            model: New LLM model
            voice_id: New voice identifier
            functions: New function definitions
            
        Returns:
            Updated assistant data
        """
        data = {}
        
        if name:
            data["name"] = name
        if first_message:
            data["firstMessage"] = first_message
        if system_prompt or model or functions:
            model_data = {}
            if model:
                model_data["provider"] = "openai"
                model_data["model"] = model
            if system_prompt:
                model_data["messages"] = [
                    {
                        "role": "system",
                        "content": system_prompt
                    }
                ]
            if functions:
                model_data["functions"] = functions
            if model_data:
                data["model"] = model_data
        if voice_id:
            data["voice"] = {
                "provider": "11labs" if settings.ELEVENLABS_API_KEY else "playht",
                "voiceId": voice_id
            }
        
        return await self._request("PATCH", f"/assistant/{assistant_id}", data=data)
    
    async def delete_assistant(self, assistant_id: str) -> Dict[str, Any]:
        """Delete a Vapi assistant.
        
        Args:
            assistant_id: Assistant ID to delete
            
        Returns:
            Deletion confirmation
        """
        return await self._request("DELETE", f"/assistant/{assistant_id}")
    
    async def get_assistant(self, assistant_id: str) -> Dict[str, Any]:
        """Get a Vapi assistant by ID.
        
        Args:
            assistant_id: Assistant ID to retrieve
            
        Returns:
            Assistant data
        """
        return await self._request("GET", f"/assistant/{assistant_id}")
    
    async def create_phone_number(
        self,
        assistant_id: str,
        phone_number: str
    ) -> Dict[str, Any]:
        """Associate a phone number with an assistant.
        
        Args:
            assistant_id: Assistant ID
            phone_number: Phone number to associate
            
        Returns:
            Phone number configuration
        """
        data = {
            "assistantId": assistant_id,
            "number": phone_number
        }
        
        return await self._request("POST", "/phone-number", data=data)
    
    async def make_outbound_call(
        self,
        assistant_id: str,
        customer_number: str,
        customer_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Initiate an outbound call.
        
        Args:
            assistant_id: Assistant ID to use for the call
            customer_number: Customer phone number to call
            customer_name: Optional customer name
            metadata: Optional metadata to attach to call
            
        Returns:
            Call initiation data with call_id
        """
        data = {
            "assistantId": assistant_id,
            "customer": {
                "number": customer_number
            }
        }
        
        if customer_name:
            data["customer"]["name"] = customer_name
        
        if metadata:
            data["metadata"] = metadata
        
        return await self._request("POST", "/call", data=data)
    
    async def get_call(self, call_id: str) -> Dict[str, Any]:
        """Get details of a specific call.
        
        Args:
            call_id: Call ID to retrieve
            
        Returns:
            Call details including status, duration, transcript
        """
        return await self._request("GET", f"/call/{call_id}")
    
    async def list_calls(
        self,
        assistant_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List calls with optional filtering.
        
        Args:
            assistant_id: Optional filter by assistant ID
            limit: Maximum number of calls to return
            offset: Number of calls to skip
            
        Returns:
            List of calls with pagination info
        """
        params = {
            "limit": limit,
            "offset": offset
        }
        
        if assistant_id:
            params["assistantId"] = assistant_id
        
        return await self._request("GET", "/call", params=params)


# Global Vapi client instance
vapi_client = VapiClient()

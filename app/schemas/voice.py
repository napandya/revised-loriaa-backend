"""Voice/Vapi schemas for voice call handling."""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID


class VapiWebhookEvent(BaseModel):
    """Schema for Vapi webhook events."""
    event_type: str  # "call.started", "call.ended", "function.called", etc.
    call_id: str
    assistant_id: Optional[str] = None
    customer_number: Optional[str] = None
    timestamp: datetime
    data: Dict[str, Any]


class VapiCallRequest(BaseModel):
    """Schema for initiating a Vapi call."""
    phone_number: str = Field(..., pattern=r"^\+?1?\d{10,15}$")
    assistant_id: str
    lead_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = None


class VapiCallResponse(BaseModel):
    """Schema for Vapi call response."""
    call_id: str
    status: str
    message: str
    started_at: Optional[datetime] = None


class VapiTranscript(BaseModel):
    """Schema for call transcript."""
    speaker: str  # "assistant" or "user"
    text: str
    timestamp: datetime


class VapiCallDetails(BaseModel):
    """Schema for detailed call information."""
    call_id: str
    status: str  # "ringing", "in-progress", "ended", "failed"
    duration_seconds: Optional[int] = None
    cost: Optional[float] = None
    transcription: List[Any] = []  # Changed from VapiTranscript to Any for flexibility
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    created_at: datetime
    ended_at: Optional[datetime] = None


class VapiAssistantConfig(BaseModel):
    """Schema for Vapi assistant configuration."""
    name: Optional[str] = None
    voice_id: Optional[str] = None
    first_message: Optional[str] = None
    system_prompt: Optional[str] = None
    model: str = "gpt-4"
    functions: Optional[List[Dict[str, Any]]] = None
    webhook_url: Optional[str] = None


class VapiFunctionCall(BaseModel):
    """Schema for Vapi function call during conversation."""
    function_name: str
    parameters: Dict[str, Any]
    call_id: str
    timestamp: datetime

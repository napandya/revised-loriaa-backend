"""Call log schemas for call tracking."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID
from app.models.call_log import CallType, CallStatus


class CallLogCreate(BaseModel):
    """Schema for creating a new call log."""
    bot_id: UUID
    bot_name: str
    start_time: datetime
    phone_number: str
    call_type: CallType
    duration_seconds: int = 0
    status: CallStatus = CallStatus.completed
    recording_url: Optional[str] = None
    transcript: Optional[str] = None


class CallLogResponse(BaseModel):
    """Schema for call log response."""
    id: UUID
    bot_id: UUID
    bot_name: str
    start_time: datetime
    phone_number: str
    call_type: CallType
    duration_seconds: int
    status: CallStatus
    recording_url: Optional[str] = None
    transcript: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

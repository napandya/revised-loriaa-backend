"""Bot schemas for bot management."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID
from app.models.bot import BotStatus


class BotBase(BaseModel):
    """Base schema for bot with common fields."""
    name: str = Field(..., min_length=1, max_length=255)
    hipaa_compliant: bool = False
    language: str = "en-US"
    status: BotStatus = BotStatus.active
    greeting_text: Optional[str] = None
    prompt: Optional[str] = None
    voice: Optional[str] = "Shimmer"
    model: Optional[str] = "gpt-4o"
    cost_per_minute: float = 0.18
    phone_number: Optional[str] = None


class BotCreate(BotBase):
    """Schema for creating a new bot."""
    pass


class BotUpdate(BaseModel):
    """Schema for updating a bot."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    hipaa_compliant: Optional[bool] = None
    language: Optional[str] = None
    status: Optional[BotStatus] = None
    greeting_text: Optional[str] = None
    prompt: Optional[str] = None
    voice: Optional[str] = None
    model: Optional[str] = None
    cost_per_minute: Optional[float] = None
    phone_number: Optional[str] = None


class BotResponse(BotBase):
    """Schema for bot response."""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

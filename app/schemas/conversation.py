"""Conversation schemas for multi-channel communications."""

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from app.models.conversation import ConversationChannel, ConversationStatus


class ConversationBase(BaseModel):
    """Base conversation schema."""
    channel: ConversationChannel
    status: ConversationStatus = ConversationStatus.open


class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation."""
    lead_id: UUID


class ConversationResponse(ConversationBase):
    """Schema for conversation response."""
    id: UUID
    lead_id: UUID
    last_message_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    """Schema for message response."""
    id: UUID
    conversation_id: UUID
    direction: str
    content: str
    sender: str
    recipient: str
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ConversationWithMessages(ConversationResponse):
    """Schema for conversation with messages list."""
    messages: List[MessageResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

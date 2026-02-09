"""Agent schemas for AI agent management."""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from app.models.agent_activity import AgentType


class AgentRequest(BaseModel):
    """Schema for agent action request."""
    agent_type: AgentType
    action: str = Field(..., min_length=1)
    lead_id: Optional[UUID] = None
    parameters: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    """Schema for agent action response."""
    success: bool
    message: str
    result: Optional[Any] = None
    activity_id: Optional[UUID] = None


class AgentTaskStatus(BaseModel):
    """Schema for agent task status."""
    task_id: UUID
    agent_type: AgentType
    status: str  # "pending", "running", "completed", "failed"
    progress: int = Field(..., ge=0, le=100)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class AgentActivityLog(BaseModel):
    """Schema for agent activity log."""
    id: UUID
    agent_type: AgentType
    action: str
    lead_id: Optional[UUID]
    metadata: Optional[Dict[str, Any]]
    result: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

"""Lead schemas for property lead management."""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from app.models.lead import LeadSource, LeadStatus


class LeadBase(BaseModel):
    """Base lead schema."""
    name: str = Field(..., min_length=1)
    email: Optional[str] = None
    phone: Optional[str] = None
    source: LeadSource
    status: LeadStatus = LeadStatus.new
    score: int = Field(default=0, ge=0)
    metadata: Optional[Dict[str, Any]] = None


class LeadCreate(LeadBase):
    """Schema for creating a new lead."""
    property_id: UUID
    user_id: UUID


class LeadUpdate(BaseModel):
    """Schema for updating a lead."""
    name: Optional[str] = Field(None, min_length=1)
    email: Optional[str] = None
    phone: Optional[str] = None
    source: Optional[LeadSource] = None
    status: Optional[LeadStatus] = None
    score: Optional[int] = Field(None, ge=0)
    metadata: Optional[Dict[str, Any]] = None


class LeadResponse(LeadBase):
    """Schema for lead response."""
    id: UUID
    property_id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class LeadActivityResponse(BaseModel):
    """Schema for lead activity response."""
    id: UUID
    lead_id: UUID
    user_id: Optional[UUID]
    activity_type: str
    description: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class LeadWithActivities(LeadResponse):
    """Schema for lead with activities list."""
    activities: List[LeadActivityResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


class LeadPipelineStats(BaseModel):
    """Schema for lead pipeline statistics."""
    total_leads: int
    new: int
    contacted: int
    qualified: int
    touring: int
    application: int
    lease: int
    move_in: int
    lost: int
    conversion_rate: float = Field(..., ge=0, le=100)
    average_score: float = Field(..., ge=0)
    leads_by_source: Dict[str, int]

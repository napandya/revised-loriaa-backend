"""Team member schemas for team management."""

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from uuid import UUID
from app.models.team import TeamRole


class TeamMemberCreate(BaseModel):
    """Schema for creating a new team member."""
    name: str
    email: EmailStr
    role: TeamRole = TeamRole.Developer
    active: bool = True


class TeamMemberUpdate(BaseModel):
    """Schema for updating a team member."""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[TeamRole] = None
    active: Optional[bool] = None


class TeamMemberResponse(BaseModel):
    """Schema for team member response."""
    id: UUID
    user_id: UUID
    name: str
    email: str
    role: TeamRole
    active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

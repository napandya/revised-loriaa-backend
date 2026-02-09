"""Team member model for user management."""

from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.database import Base


class TeamRole(str, enum.Enum):
    """Team role enumeration."""
    super_admin = "super_admin"
    admin = "admin"
    leasing_staff = "leasing_staff"
    viewer = "viewer"
    Admin = "Admin"
    Developer = "Developer"
    Support = "Support"


class TeamMember(Base):
    """Team member model for managing team members."""
    
    __tablename__ = "team_members"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True)
    role = Column(SQLEnum(TeamRole), default=TeamRole.Developer, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="team_members")

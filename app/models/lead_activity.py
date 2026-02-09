"""Lead activity model for tracking lead interactions."""

from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.database import Base


class ActivityType(str, enum.Enum):
    """Lead activity type enumeration."""
    call = "call"
    sms = "sms"
    email = "email"
    note = "note"
    status_change = "status_change"
    tour_scheduled = "tour_scheduled"


class LeadActivity(Base):
    """Lead activity model for tracking lead interactions."""
    
    __tablename__ = "lead_activities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    activity_type = Column(SQLEnum(ActivityType), nullable=False, index=True)
    description = Column(Text, nullable=True)
    extra_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    lead = relationship("Lead", back_populates="activities")
    user = relationship("User", backref="lead_activities")

"""Agent activity model for tracking AI agent actions."""

from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.database import Base


class AgentType(str, enum.Enum):
    """Agent type enumeration."""
    leasing = "leasing"
    marketing = "marketing"
    property_manager = "property_manager"


class AgentActivity(Base):
    """Agent activity model for tracking AI agent actions."""
    
    __tablename__ = "agent_activities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    agent_type = Column(SQLEnum(AgentType), nullable=False, index=True)
    action = Column(String, nullable=False)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="SET NULL"), nullable=True, index=True)
    extra_data = Column(JSON, nullable=True)
    result = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    lead = relationship("Lead", back_populates="agent_activities")

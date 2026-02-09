"""Integration configuration model for storing API keys and settings."""

from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.database import Base


class IntegrationName(str, enum.Enum):
    """Integration name enumeration."""
    vapi = "vapi"
    twilio = "twilio"
    facebook = "facebook"
    google_ads = "google_ads"
    resman = "resman"


class IntegrationConfig(Base):
    """Integration configuration model for storing API keys and settings."""
    
    __tablename__ = "integration_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    integration_name = Column(SQLEnum(IntegrationName), nullable=False, index=True)
    config = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", backref="integration_configs")

"""Lead model for property lead management."""

from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.database import Base


class LeadSource(str, enum.Enum):
    """Lead source enumeration."""
    facebook_ads = "facebook_ads"
    google_ads = "google_ads"
    website = "website"
    phone = "phone"
    referral = "referral"


class LeadStatus(str, enum.Enum):
    """Lead status enumeration."""
    new = "new"
    contacted = "contacted"
    qualified = "qualified"
    touring = "touring"
    application = "application"
    lease = "lease"
    move_in = "move_in"
    lost = "lost"


class Lead(Base):
    """Lead model for property prospects."""
    
    __tablename__ = "leads"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    property_id = Column(UUID(as_uuid=True), ForeignKey("bots.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True, index=True)
    phone = Column(String, nullable=True, index=True)
    source = Column(SQLEnum(LeadSource), nullable=False, index=True)
    status = Column(SQLEnum(LeadStatus), default=LeadStatus.new, nullable=False, index=True)
    score = Column(Integer, default=0, nullable=False)
    extra_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    property = relationship("Bot", backref="leads")
    user = relationship("User", backref="leads")
    activities = relationship("LeadActivity", back_populates="lead", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="lead", cascade="all, delete-orphan")
    agent_activities = relationship("AgentActivity", back_populates="lead", cascade="all, delete-orphan")

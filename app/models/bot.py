"""Bot model for AI voice bot configuration."""

from sqlalchemy import Column, String, Boolean, Float, DateTime, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.database import Base


class BotStatus(str, enum.Enum):
    """Bot status enumeration."""
    active = "active"
    inactive = "inactive"


class Bot(Base):
    """Bot model with configuration and settings."""
    
    __tablename__ = "bots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    hipaa_compliant = Column(Boolean, default=False, nullable=False)
    language = Column(String, default="en-US", nullable=False)
    status = Column(SQLEnum(BotStatus), default=BotStatus.active, nullable=False)
    greeting_text = Column(Text, nullable=True)
    prompt = Column(Text, nullable=True)
    voice = Column(String, default="Shimmer", nullable=True)
    model = Column(String, default="gpt-4o", nullable=True)
    cost_per_minute = Column(Float, default=0.18, nullable=False)
    phone_number = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="bots")
    call_logs = relationship("CallLog", back_populates="bot", cascade="all, delete-orphan")
    knowledge_base = relationship("KnowledgeBase", back_populates="bot", cascade="all, delete-orphan")

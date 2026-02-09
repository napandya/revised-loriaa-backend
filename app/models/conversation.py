"""Conversation model for multi-channel communications."""

from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.database import Base


class ConversationChannel(str, enum.Enum):
    """Conversation channel enumeration."""
    sms = "sms"
    email = "email"
    voice = "voice"
    chat = "chat"


class ConversationStatus(str, enum.Enum):
    """Conversation status enumeration."""
    open = "open"
    closed = "closed"


class Conversation(Base):
    """Conversation model for multi-channel communications."""
    
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    channel = Column(SQLEnum(ConversationChannel), nullable=False, index=True)
    status = Column(SQLEnum(ConversationStatus), default=ConversationStatus.open, nullable=False, index=True)
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    lead = relationship("Lead", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

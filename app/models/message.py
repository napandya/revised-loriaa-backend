"""Message model for storing conversation messages."""

from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.database import Base


class MessageDirection(str, enum.Enum):
    """Message direction enumeration."""
    inbound = "inbound"
    outbound = "outbound"


class Message(Base):
    """Message model for storing conversation messages."""
    
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    direction = Column(SQLEnum(MessageDirection), nullable=False, index=True)
    content = Column(Text, nullable=False)
    sender = Column(String, nullable=False)
    recipient = Column(String, nullable=False)
    extra_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

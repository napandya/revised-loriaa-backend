"""Call log model for tracking call records."""

from sqlalchemy import Column, String, Integer, DateTime, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.database import Base


class CallType(str, enum.Enum):
    """Call type enumeration."""
    inbound = "inbound"
    outbound = "outbound"


class CallStatus(str, enum.Enum):
    """Call status enumeration."""
    completed = "completed"
    failed = "failed"
    in_progress = "in_progress"


class CallLog(Base):
    """Call log model for tracking voice bot calls."""
    
    __tablename__ = "call_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bots.id", ondelete="CASCADE"), nullable=False, index=True)
    bot_name = Column(String, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    phone_number = Column(String, nullable=False)
    call_type = Column(SQLEnum(CallType), nullable=False)
    duration_seconds = Column(Integer, default=0, nullable=False)
    status = Column(SQLEnum(CallStatus), default=CallStatus.completed, nullable=False)
    recording_url = Column(String, nullable=True)
    transcript = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    bot = relationship("Bot", back_populates="call_logs")

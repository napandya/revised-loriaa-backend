"""Document model for knowledge base and document management."""

from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid
import enum
from app.database import Base


class DocumentCategory(str, enum.Enum):
    """Document category enumeration."""
    policy = "policy"
    procedure = "procedure"
    faq = "faq"
    training = "training"


class Document(Base):
    """Document model for knowledge base and document management."""
    
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    property_id = Column(UUID(as_uuid=True), ForeignKey("bots.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    category = Column(SQLEnum(DocumentCategory), nullable=False, index=True)
    file_url = Column(String, nullable=True)
    embedding = Column(Vector(1536), nullable=True)
    extra_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", backref="documents")
    property = relationship("Bot", backref="documents")

"""Billing record model for tracking costs."""

from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class BillingRecord(Base):
    """Billing record model for tracking monthly costs and usage."""
    
    __tablename__ = "billing_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    month = Column(String, nullable=False)  # Format: YYYY-MM
    total_cost = Column(Float, default=0.0, nullable=False)
    total_calls = Column(Integer, default=0, nullable=False)
    total_duration_minutes = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="billing_records")

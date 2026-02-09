"""Billing schemas for cost tracking."""

from pydantic import BaseModel
from datetime import datetime
from typing import List
from uuid import UUID


class MonthlyBilling(BaseModel):
    """Schema for monthly billing record."""
    id: UUID
    user_id: UUID
    month: str
    total_cost: float
    total_calls: int
    total_duration_minutes: float
    created_at: datetime
    
    class Config:
        from_attributes = True


class BillingStats(BaseModel):
    """Schema for billing statistics."""
    current_month: str
    total_cost: float
    total_calls: int
    total_duration_minutes: float
    cost_per_call: float
    cost_per_minute: float


class BillingHistory(BaseModel):
    """Schema for billing history."""
    records: List[MonthlyBilling]
    total_records: int

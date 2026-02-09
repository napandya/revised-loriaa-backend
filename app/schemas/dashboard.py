"""Dashboard schemas for COO Command Center metrics."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID


class DashboardMetrics(BaseModel):
    """Schema for overall dashboard metrics."""
    total_leads: int
    active_conversations: int
    tours_scheduled: int
    applications_pending: int
    leases_signed: int
    occupancy_rate: float = Field(..., ge=0, le=100)
    revenue_this_month: float = Field(..., ge=0)
    ai_call_minutes: int = Field(..., ge=0)
    average_response_time: float = Field(..., ge=0)
    conversion_rate: float = Field(..., ge=0, le=100)


class MarketingFunnelData(BaseModel):
    """Schema for marketing funnel analytics."""
    stage: str
    count: int
    conversion_rate: float = Field(..., ge=0, le=100)
    change_from_last_month: float


class LeasingVelocityDataPoint(BaseModel):
    """Schema for a single leasing velocity data point."""
    date: datetime
    tours: int
    applications: int
    leases: int


class LeasingVelocityData(BaseModel):
    """Schema for time series leasing velocity data."""
    data_points: List[LeasingVelocityDataPoint]
    average_days_to_lease: float = Field(..., ge=0)
    trend: str  # "up", "down", "stable"


class AgentActivityItem(BaseModel):
    """Schema for a single agent activity item."""
    id: UUID
    agent_type: str
    action: str
    lead_name: Optional[str]
    result: Optional[str]
    timestamp: datetime


class AgentActivityFeed(BaseModel):
    """Schema for agent activity feed."""
    activities: List[AgentActivityItem]
    total_actions_today: int
    total_actions_this_week: int


class PropertyHealthMetrics(BaseModel):
    """Schema for property health metrics."""
    property_id: UUID
    property_name: str
    occupancy_rate: float = Field(..., ge=0, le=100)
    lead_count: int
    active_conversations: int
    tours_this_week: int
    health_score: float = Field(..., ge=0, le=100)


class PortfolioHealthScore(BaseModel):
    """Schema for portfolio-wide health score."""
    overall_score: float = Field(..., ge=0, le=100)
    properties: List[PropertyHealthMetrics]
    total_units: int
    occupied_units: int
    portfolio_occupancy: float = Field(..., ge=0, le=100)
    properties_at_risk: int

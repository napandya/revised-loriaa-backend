"""Integration schemas for external service configurations."""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from app.models.integration_config import IntegrationName


class IntegrationConfigBase(BaseModel):
    """Base integration configuration schema."""
    integration_name: IntegrationName
    config: Dict[str, Any] = Field(..., description="Integration-specific configuration")
    is_active: bool = True


class IntegrationConfigCreate(IntegrationConfigBase):
    """Schema for creating a new integration configuration."""
    user_id: UUID


class IntegrationConfigUpdate(BaseModel):
    """Schema for updating integration configuration."""
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class IntegrationConfigResponse(IntegrationConfigBase):
    """Schema for integration configuration response."""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class FacebookLeadWebhook(BaseModel):
    """Schema for Facebook Lead Ads webhook payload."""
    entry: List[Dict[str, Any]]
    object: str = "page"


class FacebookLeadData(BaseModel):
    """Schema for parsed Facebook lead data."""
    lead_id: str
    form_id: str
    page_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    created_time: datetime
    field_data: Dict[str, Any]


class TwilioMessageWebhook(BaseModel):
    """Schema for Twilio SMS webhook payload."""
    MessageSid: str
    From: str
    To: str
    Body: str
    NumMedia: str = "0"
    MediaUrl0: Optional[str] = None
    FromCity: Optional[str] = None
    FromState: Optional[str] = None
    FromZip: Optional[str] = None


class IntegrationStatus(BaseModel):
    """Schema for integration connection status."""
    integration_name: IntegrationName
    is_active: bool
    is_connected: bool
    last_sync: Optional[datetime] = None
    error_message: Optional[str] = None
    config_valid: bool

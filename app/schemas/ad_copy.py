"""Schemas for ad copy generation and content marketing."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum


class AdPlatformEnum(str, Enum):
    """Supported advertising platforms."""
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    GOOGLE_ADS = "google_ads"
    TIKTOK = "tiktok"
    LINKEDIN = "linkedin"


class AdObjectiveEnum(str, Enum):
    """Campaign objectives."""
    LEAD_GENERATION = "lead_generation"
    BRAND_AWARENESS = "brand_awareness"
    TOUR_SCHEDULING = "tour_scheduling"
    LEASE_SIGNING = "lease_signing"
    OPEN_HOUSE = "open_house"
    SEASONAL_PROMOTION = "seasonal_promotion"
    MOVE_IN_SPECIAL = "move_in_special"


class PropertyDetailsInput(BaseModel):
    """Property details for ad copy context."""
    location: Optional[str] = None
    bedrooms: Optional[str] = Field(None, description="e.g., 'Studio, 1BR, 2BR, 3BR'")
    price_range: Optional[str] = Field(None, description="e.g., '$1,200 - $2,500/mo'")
    amenities: Optional[List[str]] = None
    pet_policy: Optional[str] = None
    unique_selling_points: Optional[List[str]] = None


class AdCopyRequest(BaseModel):
    """Request schema for generating ad copy."""
    property_name: str = Field(..., description="Name of the apartment property")
    platform: AdPlatformEnum = Field(..., description="Target ad platform")
    objective: AdObjectiveEnum = Field(
        default=AdObjectiveEnum.LEAD_GENERATION,
        description="Campaign objective"
    )
    property_details: Optional[PropertyDetailsInput] = None
    tone: str = Field(
        default="professional yet friendly",
        description="Desired tone of the ad copy"
    )
    target_audience: Optional[str] = Field(
        None,
        description="Description of the target audience"
    )
    special_offer: Optional[str] = Field(
        None,
        description="Any special promotions or move-in deals"
    )
    num_variations: int = Field(
        default=3, ge=1, le=10,
        description="Number of ad copy variations to generate"
    )


class AdCopyVariation(BaseModel):
    """A single ad copy variation."""
    headline: Optional[str] = None
    primary_text: Optional[str] = None
    description: Optional[str] = None
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None
    cta: Optional[str] = None
    headlines: Optional[List[str]] = None
    descriptions: Optional[List[str]] = None
    hook_text: Optional[str] = None
    intro_text: Optional[str] = None


class AdCopyResponse(BaseModel):
    """Response schema for generated ad copy."""
    success: bool
    property_name: str
    platform: str
    objective: str
    num_variations: int = 0
    variations: List[Dict[str, Any]] = []
    model_used: Optional[str] = None
    usage: Optional[Dict[str, int]] = None
    error: Optional[str] = None


class SocialPostRequest(BaseModel):
    """Request schema for generating social media posts."""
    property_name: str = Field(..., description="Name of the apartment property")
    platform: AdPlatformEnum = Field(..., description="Target social media platform")
    topic: str = Field(
        ...,
        description="Post topic (e.g., 'community event', 'amenity spotlight')"
    )
    property_details: Optional[PropertyDetailsInput] = None
    tone: str = Field(default="engaging and casual")


class SocialPostResponse(BaseModel):
    """Response schema for generated social media post."""
    success: bool
    property_name: str
    platform: str
    topic: str
    post: Optional[Dict[str, Any]] = None
    model_used: Optional[str] = None
    error: Optional[str] = None


class ImproveAdCopyRequest(BaseModel):
    """Request schema for improving existing ad copy."""
    existing_copy: str = Field(..., description="The current ad copy to improve")
    platform: AdPlatformEnum = Field(..., description="Target platform")
    feedback: Optional[str] = Field(
        None,
        description="Human feedback on what to change"
    )
    performance_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Campaign metrics (CTR, CPC, etc.)"
    )


class ImproveAdCopyResponse(BaseModel):
    """Response schema for improved ad copy."""
    success: bool
    platform: str
    original_copy: str
    improved_copy: Optional[str] = None
    changes_made: Optional[List[str]] = None
    expected_improvement: Optional[str] = None
    model_used: Optional[str] = None
    error: Optional[str] = None


class CampaignStrategyRequest(BaseModel):
    """Request schema for generating a campaign strategy."""
    property_name: str = Field(..., description="Property name")
    budget: float = Field(..., gt=0, description="Total campaign budget in dollars")
    platforms: List[AdPlatformEnum] = Field(
        ...,
        description="Target platforms"
    )
    property_details: Optional[PropertyDetailsInput] = None
    goals: Optional[str] = Field(
        None,
        description="Campaign goals description"
    )
    timeline: str = Field(
        default="30 days",
        description="Campaign timeline"
    )


class CampaignStrategyResponse(BaseModel):
    """Response schema for campaign strategy."""
    success: bool
    property_name: str
    budget: float
    platforms: List[str]
    timeline: str
    strategy: Optional[Dict[str, Any]] = None
    model_used: Optional[str] = None
    error: Optional[str] = None

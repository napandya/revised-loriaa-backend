"""Ad copy generation API endpoints using ChatGPT / OpenAI."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.schemas.ad_copy import (
    AdCopyRequest,
    AdCopyResponse,
    SocialPostRequest,
    SocialPostResponse,
    ImproveAdCopyRequest,
    ImproveAdCopyResponse,
    CampaignStrategyRequest,
    CampaignStrategyResponse,
)
from app.services.content_generation_service import (
    generate_ad_copy,
    generate_social_media_post,
    improve_ad_copy,
    generate_campaign_strategy,
)

router = APIRouter()


@router.post("/generate", response_model=AdCopyResponse)
async def generate_ad_copy_endpoint(
    request: AdCopyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate advertising copy for a specific platform using ChatGPT.

    Supports Facebook, Instagram, Google Ads, TikTok, and LinkedIn.
    Returns multiple ad copy variations optimized for the chosen platform and objective.
    """
    try:
        result = await generate_ad_copy(
            property_name=request.property_name,
            platform=request.platform.value,
            objective=request.objective.value,
            property_details=request.property_details.model_dump(exclude_none=True) if request.property_details else None,
            tone=request.tone,
            target_audience=request.target_audience,
            special_offer=request.special_offer,
            num_variations=request.num_variations,
        )

        return AdCopyResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ad copy generation failed: {str(e)}",
        )


@router.post("/social-post", response_model=SocialPostResponse)
async def generate_social_post_endpoint(
    request: SocialPostRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate an organic social media post (not paid ad) for a property.

    Ideal for community engagement, amenity spotlights, and resident content.
    """
    try:
        result = await generate_social_media_post(
            property_name=request.property_name,
            platform=request.platform.value,
            topic=request.topic,
            property_details=request.property_details.model_dump(exclude_none=True) if request.property_details else None,
            tone=request.tone,
        )

        return SocialPostResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Social post generation failed: {str(e)}",
        )


@router.post("/improve", response_model=ImproveAdCopyResponse)
async def improve_ad_copy_endpoint(
    request: ImproveAdCopyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Improve existing ad copy based on feedback or performance data.

    Provide the current copy and optionally include campaign performance
    metrics (CTR, CPC, etc.) for data-driven improvements.
    """
    try:
        result = await improve_ad_copy(
            existing_copy=request.existing_copy,
            platform=request.platform.value,
            feedback=request.feedback,
            performance_data=request.performance_data,
        )

        return ImproveAdCopyResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ad copy improvement failed: {str(e)}",
        )


@router.post("/campaign-strategy", response_model=CampaignStrategyResponse)
async def generate_campaign_strategy_endpoint(
    request: CampaignStrategyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate a comprehensive multi-platform advertising campaign strategy.

    Includes budget allocation, per-platform ad copy, targeting recommendations,
    and KPI benchmarks — all powered by ChatGPT.
    """
    try:
        result = await generate_campaign_strategy(
            property_name=request.property_name,
            budget=request.budget,
            platforms=[p.value for p in request.platforms],
            property_details=request.property_details.model_dump(exclude_none=True) if request.property_details else None,
            goals=request.goals,
            timeline=request.timeline,
        )

        return CampaignStrategyResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Campaign strategy generation failed: {str(e)}",
        )

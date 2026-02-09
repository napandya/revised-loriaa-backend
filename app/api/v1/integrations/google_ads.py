"""Google Ads integration API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.integrations.google_ads.client import GoogleAdsClient

router = APIRouter(prefix="/integrations/google-ads", tags=["integrations", "google-ads"])


@router.get("/campaigns")
async def list_google_campaigns(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List Google Ads campaigns."""
    try:
        client = GoogleAdsClient(db=db, user_id=current_user.id)
        campaigns = client.get_campaigns()
        return {"campaigns": campaigns}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch campaigns: {str(e)}"
        )


@router.get("/campaigns/{campaign_id}/performance")
async def get_campaign_performance(
    campaign_id: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get Google Ads campaign performance metrics."""
    try:
        client = GoogleAdsClient(db=db, user_id=current_user.id)
        performance = client.get_campaign_performance(
            campaign_id=campaign_id,
            date_from=date_from,
            date_to=date_to
        )
        return {"performance": performance}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch performance: {str(e)}"
        )


@router.post("/conversions")
async def track_conversion(
    conversion_name: str,
    conversion_time: str,
    conversion_value: Optional[float] = None,
    gclid: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Track Google Ads conversion."""
    try:
        client = GoogleAdsClient(db=db, user_id=current_user.id)
        result = client.track_conversion(
            conversion_name=conversion_name,
            conversion_time=conversion_time,
            conversion_value=conversion_value,
            gclid=gclid
        )
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversion tracking failed: {str(e)}"
        )

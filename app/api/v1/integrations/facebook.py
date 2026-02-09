"""Facebook Ads integration API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.integrations.facebook.client import FacebookAdsClient
from app.integrations.facebook.campaigns import get_campaigns, get_campaign_insights
from app.integrations.facebook.leads import process_lead_webhook
from app.schemas.integration import FacebookLeadWebhook

router = APIRouter(prefix="/integrations/facebook", tags=["integrations", "facebook"])


@router.get("/campaigns")
async def list_facebook_campaigns(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List Facebook ad campaigns."""
    try:
        client = FacebookAdsClient(db=db, user_id=current_user.id)
        campaigns = get_campaigns(client)
        return {"campaigns": campaigns}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch campaigns: {str(e)}"
        )


@router.get("/campaigns/{campaign_id}/insights")
async def get_campaign_insights_data(
    campaign_id: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get Facebook campaign insights."""
    try:
        client = FacebookAdsClient(db=db, user_id=current_user.id)
        insights = get_campaign_insights(
            client,
            campaign_id=campaign_id,
            date_from=date_from,
            date_to=date_to
        )
        return {"insights": insights}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch insights: {str(e)}"
        )


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def facebook_lead_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Facebook Lead Ads webhook (no auth required)."""
    try:
        data = await request.json()
        webhook_data = FacebookLeadWebhook(**data)
        
        result = process_lead_webhook(db=db, webhook_data=webhook_data)
        
        return {"status": "success", "processed": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}"
        )


@router.get("/webhook")
async def facebook_webhook_verification(
    hub_mode: str = None,
    hub_verify_token: str = None,
    hub_challenge: str = None
):
    """Facebook webhook verification."""
    import os
    
    verify_token = os.getenv("FACEBOOK_VERIFY_TOKEN", "loriaa_verify_token")
    
    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        return int(hub_challenge)
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid verification token"
    )

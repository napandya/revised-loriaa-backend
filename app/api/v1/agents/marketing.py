"""Marketing agent API endpoints for campaign analysis and optimization."""

from typing import Optional, Dict, Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.agents.workforce.marketing_agent import MarketingAgent
from app.schemas.agent import AgentResponse

router = APIRouter(prefix="/agents/marketing", tags=["agents", "marketing"])


@router.post("/execute", response_model=AgentResponse)
async def execute_marketing_task(
    action: str,
    parameters: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Execute marketing agent task."""
    agent = MarketingAgent()
    
    try:
        result = agent.execute_task(
            db=db,
            action=action,
            parameters=parameters or {},
            user_id=current_user.id
        )
        
        return AgentResponse(
            success=True,
            message=f"Marketing agent executed: {action}",
            result=result
        )
    except Exception as e:
        return AgentResponse(
            success=False,
            message=f"Marketing agent error: {str(e)}",
            result=None
        )


@router.post("/analyze-campaign", response_model=AgentResponse)
async def analyze_campaign(
    campaign_id: str,
    platform: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyze marketing campaign performance."""
    agent = MarketingAgent()
    
    try:
        result = agent.analyze_campaign(
            db=db,
            campaign_id=campaign_id,
            platform=platform,
            user_id=current_user.id
        )
        
        return AgentResponse(
            success=True,
            message="Campaign analysis completed",
            result=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Campaign analysis failed: {str(e)}"
        )


@router.post("/optimize-budget", response_model=AgentResponse)
async def optimize_budget(
    total_budget: float,
    platforms: list[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get budget optimization recommendations."""
    agent = MarketingAgent()
    
    try:
        result = agent.optimize_budget(
            db=db,
            total_budget=total_budget,
            platforms=platforms,
            user_id=current_user.id
        )
        
        return AgentResponse(
            success=True,
            message="Budget optimization completed",
            result=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Budget optimization failed: {str(e)}"
        )


@router.get("/activity")
async def get_activity_log(
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get marketing agent activity log."""
    from app.models.agent_activity import AgentActivity, AgentType
    
    activities = db.query(AgentActivity).filter(
        AgentActivity.agent_type == AgentType.marketing,
        AgentActivity.user_id == current_user.id
    ).order_by(
        AgentActivity.created_at.desc()
    ).limit(limit).all()
    
    return {"activities": activities, "count": len(activities)}


@router.post("/generate-ad-copy", response_model=AgentResponse)
async def generate_ad_copy(
    property_name: str,
    platform: str = "facebook",
    objective: str = "lead_generation",
    special_offer: Optional[str] = None,
    num_variations: int = 3,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate advertising copy for a given platform using ChatGPT.
    
    The MarketingAgent uses OpenAI to create compelling ad copy variations
    for Facebook, Instagram, Google Ads, TikTok, or LinkedIn.
    """
    from app.services.content_generation_service import generate_ad_copy as gen_copy

    try:
        result = await gen_copy(
            property_name=property_name,
            platform=platform,
            objective=objective,
            special_offer=special_offer,
            num_variations=num_variations,
        )

        return AgentResponse(
            success=result.get("success", False),
            message=f"Generated {result.get('num_variations', 0)} ad copy variations for {platform}",
            result=result
        )
    except Exception as e:
        return AgentResponse(
            success=False,
            message=f"Ad copy generation failed: {str(e)}",
            result=None
        )

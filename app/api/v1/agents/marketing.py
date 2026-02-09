"""Marketing agent API endpoints for campaign analysis and optimization."""

from typing import Optional, Dict, Any
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

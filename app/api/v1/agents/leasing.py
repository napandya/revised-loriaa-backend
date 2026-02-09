"""Leasing agent API endpoints for lead qualification and tours."""

from typing import Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.agents.workforce.leasing_agent import LeasingAgent
from app.schemas.agent import AgentResponse

router = APIRouter(prefix="/agents/leasing", tags=["agents", "leasing"])


@router.post("/execute", response_model=AgentResponse)
async def execute_leasing_task(
    action: str,
    lead_id: Optional[UUID] = None,
    parameters: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Execute leasing agent task."""
    agent = LeasingAgent()
    
    try:
        result = agent.execute_task(
            db=db,
            action=action,
            lead_id=lead_id,
            parameters=parameters or {},
            user_id=current_user.id
        )
        
        return AgentResponse(
            success=True,
            message=f"Leasing agent executed: {action}",
            result=result
        )
    except Exception as e:
        return AgentResponse(
            success=False,
            message=f"Leasing agent error: {str(e)}",
            result=None
        )


@router.post("/qualify-lead", response_model=AgentResponse)
async def qualify_lead(
    lead_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Qualify a lead using leasing agent."""
    agent = LeasingAgent()
    
    try:
        result = agent.qualify_lead(db=db, lead_id=lead_id, user_id=current_user.id)
        
        return AgentResponse(
            success=True,
            message="Lead qualification completed",
            result=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lead qualification failed: {str(e)}"
        )


@router.post("/schedule-tour", response_model=AgentResponse)
async def schedule_tour(
    lead_id: UUID,
    tour_date: str,
    tour_time: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Schedule tour for a lead."""
    agent = LeasingAgent()
    
    try:
        result = agent.schedule_tour(
            db=db,
            lead_id=lead_id,
            tour_date=tour_date,
            tour_time=tour_time,
            user_id=current_user.id
        )
        
        return AgentResponse(
            success=True,
            message="Tour scheduled successfully",
            result=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tour scheduling failed: {str(e)}"
        )


@router.get("/activity")
async def get_activity_log(
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get leasing agent activity log."""
    from app.models.agent_activity import AgentActivity, AgentType
    
    activities = db.query(AgentActivity).filter(
        AgentActivity.agent_type == AgentType.leasing,
        AgentActivity.user_id == current_user.id
    ).order_by(
        AgentActivity.created_at.desc()
    ).limit(limit).all()
    
    return {"activities": activities, "count": len(activities)}

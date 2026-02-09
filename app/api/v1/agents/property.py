"""Property manager agent API endpoints for property operations."""

from typing import Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.agents.workforce.property_agent import PropertyAgent
from app.schemas.agent import AgentResponse

router = APIRouter(prefix="/agents/property", tags=["agents", "property"])


@router.post("/execute", response_model=AgentResponse)
async def execute_property_task(
    action: str,
    property_id: Optional[UUID] = None,
    parameters: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Execute property manager agent task."""
    agent = PropertyAgent()
    
    try:
        result = agent.execute_task(
            db=db,
            action=action,
            property_id=property_id,
            parameters=parameters or {},
            user_id=current_user.id
        )
        
        return AgentResponse(
            success=True,
            message=f"Property agent executed: {action}",
            result=result
        )
    except Exception as e:
        return AgentResponse(
            success=False,
            message=f"Property agent error: {str(e)}",
            result=None
        )


@router.post("/query", response_model=AgentResponse)
async def query_property_agent(
    query: str,
    property_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ask property management question."""
    agent = PropertyAgent()
    
    try:
        result = agent.answer_query(
            db=db,
            query=query,
            property_id=property_id,
            user_id=current_user.id
        )
        
        return AgentResponse(
            success=True,
            message="Query answered",
            result=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}"
        )


@router.get("/activity")
async def get_activity_log(
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get property agent activity log."""
    from app.models.agent_activity import AgentActivity, AgentType
    
    activities = db.query(AgentActivity).filter(
        AgentActivity.agent_type == AgentType.property,
        AgentActivity.user_id == current_user.id
    ).order_by(
        AgentActivity.created_at.desc()
    ).limit(limit).all()
    
    return {"activities": activities, "count": len(activities)}

"""Lead management API endpoints for CRUD and pipeline operations."""

from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.lead import LeadStatus, LeadSource
from app.schemas.lead import (
    LeadCreate,
    LeadUpdate,
    LeadResponse,
    LeadWithActivities,
    LeadPipelineStats,
)
from app.services.lead_service import (
    create_lead,
    get_lead,
    get_leads,
    update_lead,
    delete_lead,
    update_lead_status,
    add_lead_activity,
    get_pipeline_stats,
)

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("", response_model=List[LeadResponse])
async def list_leads(
    status: Optional[LeadStatus] = None,
    source: Optional[LeadSource] = None,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List leads with optional filters and pagination."""
    filters = {}
    if status:
        filters['status'] = status
    if source:
        filters['source'] = source
    if search:
        filters['search'] = search
    if date_from:
        filters['date_from'] = date_from
    if date_to:
        filters['date_to'] = date_to
    
    leads = get_leads(
        db=db,
        user_id=current_user.id,
        filters=filters,
        skip=skip,
        limit=limit
    )
    return leads


@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_new_lead(
    lead_data: LeadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new lead."""
    lead = create_lead(db=db, lead_data=lead_data)
    return lead


@router.get("/{lead_id}", response_model=LeadWithActivities)
async def get_lead_details(
    lead_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get lead details with activities."""
    lead = get_lead(db=db, lead_id=lead_id, include_activities=True)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    return lead


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead_details(
    lead_id: UUID,
    lead_data: LeadUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update lead details."""
    lead = update_lead(db=db, lead_id=lead_id, lead_data=lead_data)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    return lead


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead_by_id(
    lead_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a lead."""
    success = delete_lead(db=db, lead_id=lead_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    return None


@router.patch("/{lead_id}/status", response_model=LeadResponse)
async def change_lead_status(
    lead_id: UUID,
    new_status: LeadStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update lead status."""
    lead = update_lead_status(
        db=db,
        lead_id=lead_id,
        new_status=new_status,
        user_id=current_user.id
    )
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    return lead


@router.post("/{lead_id}/activities", status_code=status.HTTP_201_CREATED)
async def add_activity(
    lead_id: UUID,
    activity_type: str,
    description: Optional[str] = None,
    metadata: Optional[dict] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add activity to a lead."""
    activity = add_lead_activity(
        db=db,
        lead_id=lead_id,
        activity_type=activity_type,
        description=description,
        metadata=metadata,
        user_id=current_user.id
    )
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    return activity


@router.get("/pipeline/stats", response_model=LeadPipelineStats)
async def get_pipeline_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get pipeline statistics."""
    stats = get_pipeline_stats(db=db, user_id=current_user.id)
    return stats

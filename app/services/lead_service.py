"""Lead management service with business logic."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.lead import Lead, LeadStatus, LeadSource
from app.models.lead_activity import LeadActivity, ActivityType
from app.schemas.lead import (
    LeadCreate,
    LeadUpdate,
    LeadResponse,
    LeadPipelineStats,
    LeadWithActivities
)
from app.core.exceptions import NotFoundError, ValidationError, DatabaseError


async def create_lead(db: Session, lead_data: LeadCreate) -> Lead:
    """
    Create a new lead with initial scoring.
    
    Args:
        db: Database session
        lead_data: Lead creation data
        
    Returns:
        Created lead instance
        
    Raises:
        DatabaseError: If database operation fails
    """
    try:
        lead = Lead(**lead_data.model_dump())
        db.add(lead)
        db.commit()
        db.refresh(lead)
        
        # Create initial activity
        activity = LeadActivity(
            lead_id=lead.id,
            user_id=lead.user_id,
            activity_type=ActivityType.status_change,
            description=f"Lead created from {lead.source.value}",
            metadata={"status": LeadStatus.new.value}
        )
        db.add(activity)
        db.commit()
        
        return lead
    except Exception as e:
        db.rollback()
        raise DatabaseError(f"Failed to create lead: {str(e)}")


async def update_lead(db: Session, lead_id: UUID, lead_data: LeadUpdate) -> Lead:
    """
    Update an existing lead.
    
    Args:
        db: Database session
        lead_id: Lead UUID
        lead_data: Lead update data
        
    Returns:
        Updated lead instance
        
    Raises:
        NotFoundError: If lead not found
        DatabaseError: If database operation fails
    """
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise NotFoundError(f"Lead with ID {lead_id} not found", "Lead")
        
        update_dict = lead_data.model_dump(exclude_unset=True)
        
        # Track status changes
        old_status = lead.status
        for key, value in update_dict.items():
            setattr(lead, key, value)
        
        db.commit()
        db.refresh(lead)
        
        # Create activity for status change
        if "status" in update_dict and old_status != lead.status:
            activity = LeadActivity(
                lead_id=lead.id,
                user_id=lead.user_id,
                activity_type=ActivityType.status_change,
                description=f"Status changed from {old_status.value} to {lead.status.value}",
                metadata={"old_status": old_status.value, "new_status": lead.status.value}
            )
            db.add(activity)
            db.commit()
        
        return lead
    except NotFoundError:
        raise
    except Exception as e:
        db.rollback()
        raise DatabaseError(f"Failed to update lead: {str(e)}")


async def get_lead(db: Session, lead_id: UUID) -> Lead:
    """
    Get a lead by ID.
    
    Args:
        db: Database session
        lead_id: Lead UUID
        
    Returns:
        Lead instance
        
    Raises:
        NotFoundError: If lead not found
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise NotFoundError(f"Lead with ID {lead_id} not found", "Lead")
    return lead


async def list_leads(
    db: Session,
    property_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    status: Optional[LeadStatus] = None,
    source: Optional[LeadSource] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Lead]:
    """
    List leads with optional filters.
    
    Args:
        db: Database session
        property_id: Filter by property
        user_id: Filter by user
        status: Filter by status
        source: Filter by source
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of leads
    """
    query = db.query(Lead)
    
    if property_id:
        query = query.filter(Lead.property_id == property_id)
    if user_id:
        query = query.filter(Lead.user_id == user_id)
    if status:
        query = query.filter(Lead.status == status)
    if source:
        query = query.filter(Lead.source == source)
    
    query = query.order_by(Lead.created_at.desc())
    return query.offset(skip).limit(limit).all()


def get_leads(
    db: Session,
    user_id: Optional[UUID] = None,
    filters: Optional[Dict[str, Any]] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Lead]:
    """
    Get leads with filters (synchronous version for API).
    
    Args:
        db: Database session
        user_id: Filter by user
        filters: Optional dictionary of filters (status, source, search, date_from, date_to)
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of leads
    """
    query = db.query(Lead)
    
    if user_id:
        query = query.filter(Lead.user_id == user_id)
    
    if filters:
        if filters.get('status'):
            query = query.filter(Lead.status == filters['status'])
        if filters.get('source'):
            query = query.filter(Lead.source == filters['source'])
        if filters.get('search'):
            search_term = f"%{filters['search']}%"
            query = query.filter(
                (Lead.name.ilike(search_term)) |
                (Lead.email.ilike(search_term)) |
                (Lead.phone.ilike(search_term))
            )
        if filters.get('date_from'):
            query = query.filter(Lead.created_at >= filters['date_from'])
        if filters.get('date_to'):
            query = query.filter(Lead.created_at <= filters['date_to'])
    
    query = query.order_by(Lead.created_at.desc())
    return query.offset(skip).limit(limit).all()


def delete_lead(db: Session, lead_id: UUID) -> bool:
    """
    Delete a lead by ID.
    
    Args:
        db: Database session
        lead_id: Lead UUID
        
    Returns:
        True if deleted, False if not found
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        return False
    
    # Delete associated activities first
    db.query(LeadActivity).filter(LeadActivity.lead_id == lead_id).delete()
    db.delete(lead)
    db.commit()
    return True


def add_lead_activity(
    db: Session,
    lead_id: UUID,
    activity_type: str,
    description: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    user_id: Optional[UUID] = None
) -> Optional[LeadActivity]:
    """
    Add an activity to a lead.
    
    Args:
        db: Database session
        lead_id: Lead UUID
        activity_type: Type of activity
        description: Activity description
        metadata: Additional metadata
        user_id: User who performed the activity
        
    Returns:
        Created activity or None if lead not found
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        return None
    
    try:
        activity_type_enum = ActivityType(activity_type)
    except ValueError:
        activity_type_enum = ActivityType.note
    
    activity = LeadActivity(
        lead_id=lead_id,
        user_id=user_id or lead.user_id,
        activity_type=activity_type_enum,
        description=description or f"Activity: {activity_type}",
        metadata=metadata or {}
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


async def update_lead_status(
    db: Session,
    lead_id: UUID,
    new_status: LeadStatus,
    user_id: Optional[UUID] = None,
    notes: Optional[str] = None
) -> Lead:
    """
    Update lead status and create activity record.
    
    Args:
        db: Database session
        lead_id: Lead UUID
        new_status: New lead status
        user_id: User making the change
        notes: Optional notes about the status change
        
    Returns:
        Updated lead instance
        
    Raises:
        NotFoundError: If lead not found
        DatabaseError: If database operation fails
    """
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise NotFoundError(f"Lead with ID {lead_id} not found", "Lead")
        
        old_status = lead.status
        lead.status = new_status
        db.commit()
        db.refresh(lead)
        
        # Create activity record
        activity = LeadActivity(
            lead_id=lead.id,
            user_id=user_id or lead.user_id,
            activity_type=ActivityType.status_change,
            description=notes or f"Status changed from {old_status.value} to {new_status.value}",
            metadata={
                "old_status": old_status.value,
                "new_status": new_status.value
            }
        )
        db.add(activity)
        db.commit()
        
        return lead
    except NotFoundError:
        raise
    except Exception as e:
        db.rollback()
        raise DatabaseError(f"Failed to update lead status: {str(e)}")


async def get_pipeline_stats(
    db: Session,
    property_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None
) -> LeadPipelineStats:
    """
    Calculate pipeline statistics for leads.
    
    Args:
        db: Database session
        property_id: Filter by property
        user_id: Filter by user
        
    Returns:
        Pipeline statistics
    """
    query = db.query(Lead)
    
    if property_id:
        query = query.filter(Lead.property_id == property_id)
    if user_id:
        query = query.filter(Lead.user_id == user_id)
    
    total_leads = query.count()
    
    # Count by status
    status_counts = {}
    for status in LeadStatus:
        count = query.filter(Lead.status == status).count()
        status_counts[status.value] = count
    
    # Count by source
    leads_by_source = {}
    for source in LeadSource:
        count = query.filter(Lead.source == source).count()
        if count > 0:
            leads_by_source[source.value] = count
    
    # Calculate conversion rate (leads that reached lease or move_in)
    converted = query.filter(
        Lead.status.in_([LeadStatus.lease, LeadStatus.move_in])
    ).count()
    conversion_rate = (converted / total_leads * 100) if total_leads > 0 else 0.0
    
    # Calculate average score
    avg_score_result = query.with_entities(func.avg(Lead.score)).scalar()
    average_score = float(avg_score_result) if avg_score_result else 0.0
    
    return LeadPipelineStats(
        total_leads=total_leads,
        new=status_counts.get("new", 0),
        contacted=status_counts.get("contacted", 0),
        qualified=status_counts.get("qualified", 0),
        touring=status_counts.get("touring", 0),
        application=status_counts.get("application", 0),
        lease=status_counts.get("lease", 0),
        move_in=status_counts.get("move_in", 0),
        lost=status_counts.get("lost", 0),
        conversion_rate=conversion_rate,
        average_score=average_score,
        leads_by_source=leads_by_source
    )


def calculate_lead_score_internal(lead: Lead, activity_count: int) -> int:
    """
    Calculate lead score based on various factors.
    
    Args:
        lead: Lead instance
        activity_count: Number of activities for the lead
        
    Returns:
        Score between 0-100
    """
    score = 0
    
    # Source quality (0-30 points)
    source_scores = {
        LeadSource.referral: 30,
        LeadSource.website: 25,
        LeadSource.google_ads: 20,
        LeadSource.facebook_ads: 15,
        LeadSource.phone: 20
    }
    score += source_scores.get(lead.source, 10)
    
    # Status progression (0-30 points)
    status_scores = {
        LeadStatus.new: 5,
        LeadStatus.contacted: 10,
        LeadStatus.qualified: 15,
        LeadStatus.touring: 20,
        LeadStatus.application: 25,
        LeadStatus.lease: 30,
        LeadStatus.move_in: 30,
        LeadStatus.lost: 0
    }
    score += status_scores.get(lead.status, 0)
    
    # Engagement level (0-25 points)
    if activity_count >= 10:
        score += 25
    elif activity_count >= 5:
        score += 20
    elif activity_count >= 3:
        score += 15
    elif activity_count >= 1:
        score += 10
    
    # Contact information completeness (0-15 points)
    if lead.email:
        score += 8
    if lead.phone:
        score += 7
    
    return min(score, 100)

"""Lead management tools for agents."""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.models.lead import Lead
from app.models.lead_activity import LeadActivity

logger = logging.getLogger(__name__)


def get_lead_info(lead_id: str, db: Session) -> Dict[str, Any]:
    """
    Get comprehensive lead information.
    
    Args:
        lead_id: UUID of the lead
        db: Database session
    
    Returns:
        Dict with lead details
    """
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        
        if not lead:
            return {"error": f"Lead {lead_id} not found"}
        
        return {
            "id": str(lead.id),
            "name": lead.name,
            "email": lead.email,
            "phone": lead.phone,
            "status": lead.status,
            "source": lead.source,
            "score": lead.score,
            "move_in_date": lead.move_in_date.isoformat() if lead.move_in_date else None,
            "budget_min": lead.budget_min,
            "budget_max": lead.budget_max,
            "bedrooms": lead.bedrooms,
            "notes": lead.notes,
            "created_at": lead.created_at.isoformat(),
            "updated_at": lead.updated_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting lead info: {str(e)}")
        return {"error": str(e)}


def update_lead_status(lead_id: str, status: str, db: Session) -> Dict[str, Any]:
    """
    Update lead status.
    
    Args:
        lead_id: UUID of the lead
        status: New status value
        db: Database session
    
    Returns:
        Dict with update result
    """
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        
        if not lead:
            return {"error": f"Lead {lead_id} not found"}
        
        old_status = lead.status
        lead.status = status
        lead.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(lead)
        
        # Log the status change
        activity = LeadActivity(
            lead_id=lead_id,
            activity_type="status_change",
            description=f"Status changed from {old_status} to {status}",
            metadata={"old_status": old_status, "new_status": status}
        )
        db.add(activity)
        db.commit()
        
        return {
            "success": True,
            "lead_id": lead_id,
            "old_status": old_status,
            "new_status": status,
            "message": f"Lead status updated to {status}"
        }
    except Exception as e:
        logger.error(f"Error updating lead status: {str(e)}")
        db.rollback()
        return {"error": str(e)}


def score_lead(lead_id: str, db: Session) -> Dict[str, Any]:
    """
    Calculate and update lead score.
    
    Args:
        lead_id: UUID of the lead
        db: Database session
    
    Returns:
        Dict with score details
    """
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        
        if not lead:
            return {"error": f"Lead {lead_id} not found"}
        
        # Simple scoring logic (can be enhanced)
        score = 0
        factors = []
        
        # Has contact info
        if lead.email:
            score += 20
            factors.append("email_provided")
        if lead.phone:
            score += 20
            factors.append("phone_provided")
        
        # Has budget info
        if lead.budget_min and lead.budget_max:
            score += 25
            factors.append("budget_specified")
        
        # Has move-in date
        if lead.move_in_date:
            score += 20
            factors.append("move_in_date_set")
            
            # Urgent move-in (within 30 days)
            days_until = (lead.move_in_date - datetime.utcnow().date()).days
            if 0 < days_until <= 30:
                score += 15
                factors.append("urgent_timeline")
        
        # Update lead score
        lead.score = score
        lead.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "success": True,
            "lead_id": lead_id,
            "score": score,
            "factors": factors,
            "message": f"Lead scored at {score}/100"
        }
    except Exception as e:
        logger.error(f"Error scoring lead: {str(e)}")
        db.rollback()
        return {"error": str(e)}


def assign_lead(lead_id: str, user_id: str, db: Session) -> Dict[str, Any]:
    """
    Assign lead to a user.
    
    Args:
        lead_id: UUID of the lead
        user_id: UUID of the user to assign to
        db: Database session
    
    Returns:
        Dict with assignment result
    """
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        
        if not lead:
            return {"error": f"Lead {lead_id} not found"}
        
        old_assignee = lead.assigned_to
        lead.assigned_to = user_id
        lead.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Log the assignment
        activity = LeadActivity(
            lead_id=lead_id,
            activity_type="assignment",
            description=f"Lead assigned to user {user_id}",
            metadata={"old_assignee": old_assignee, "new_assignee": user_id}
        )
        db.add(activity)
        db.commit()
        
        return {
            "success": True,
            "lead_id": lead_id,
            "assigned_to": user_id,
            "message": f"Lead assigned to user {user_id}"
        }
    except Exception as e:
        logger.error(f"Error assigning lead: {str(e)}")
        db.rollback()
        return {"error": str(e)}


def create_lead_note(lead_id: str, note: str, db: Session) -> Dict[str, Any]:
    """
    Create a note for a lead.
    
    Args:
        lead_id: UUID of the lead
        note: Note content
        db: Database session
    
    Returns:
        Dict with note creation result
    """
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        
        if not lead:
            return {"error": f"Lead {lead_id} not found"}
        
        # Add note to lead notes (append to existing)
        current_notes = lead.notes or ""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        new_note = f"\n[{timestamp}] {note}"
        lead.notes = current_notes + new_note
        lead.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Log the note activity
        activity = LeadActivity(
            lead_id=lead_id,
            activity_type="note_added",
            description="Note added to lead",
            metadata={"note": note}
        )
        db.add(activity)
        db.commit()
        
        return {
            "success": True,
            "lead_id": lead_id,
            "note": note,
            "message": "Note added successfully"
        }
    except Exception as e:
        logger.error(f"Error creating lead note: {str(e)}")
        db.rollback()
        return {"error": str(e)}

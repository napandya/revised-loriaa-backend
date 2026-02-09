"""Scheduling tools for agents."""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date, time
import logging
import uuid

from app.models.lead_activity import LeadActivity

logger = logging.getLogger(__name__)

# In-memory tour storage (replace with database model in production)
TOURS = {}


def check_availability(
    date_str: str,
    time_slot: str,
    property_id: str = None,
    db: Session = None
) -> Dict[str, Any]:
    """
    Check availability for a tour time slot.
    
    Args:
        date_str: Date in YYYY-MM-DD format
        time_slot: Time slot (e.g., "10:00 AM", "2:30 PM")
        property_id: Optional property ID
        db: Optional database session
    
    Returns:
        Dict with availability status
    """
    try:
        # Parse date
        tour_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        # Check if date is in the past
        if tour_date < datetime.utcnow().date():
            return {
                "available": False,
                "reason": "Date is in the past",
                "date": date_str,
                "time_slot": time_slot
            }
        
        # Check if date is too far in future (e.g., > 60 days)
        max_date = datetime.utcnow().date() + timedelta(days=60)
        if tour_date > max_date:
            return {
                "available": False,
                "reason": "Date is too far in the future (max 60 days)",
                "date": date_str,
                "time_slot": time_slot
            }
        
        # Check existing tours (simple logic - max 3 tours per hour)
        key = f"{date_str}_{time_slot}_{property_id or 'all'}"
        existing_count = sum(1 for t in TOURS.values() 
                           if t.get("date") == date_str 
                           and t.get("time_slot") == time_slot
                           and (not property_id or t.get("property_id") == property_id))
        
        if existing_count >= 3:
            return {
                "available": False,
                "reason": "Time slot is fully booked",
                "date": date_str,
                "time_slot": time_slot,
                "existing_tours": existing_count
            }
        
        return {
            "available": True,
            "date": date_str,
            "time_slot": time_slot,
            "property_id": property_id,
            "message": "Time slot is available"
        }
        
    except Exception as e:
        logger.error(f"Error checking availability: {str(e)}")
        return {
            "available": False,
            "error": str(e)
        }


def schedule_tour(
    lead_id: str,
    date_str: str,
    time_slot: str,
    property_id: str,
    db: Session,
    notes: str = None
) -> Dict[str, Any]:
    """
    Schedule a tour for a lead.
    
    Args:
        lead_id: UUID of the lead
        date_str: Date in YYYY-MM-DD format
        time_slot: Time slot
        property_id: Property ID
        db: Database session
        notes: Optional notes about the tour
    
    Returns:
        Dict with scheduling result
    """
    try:
        # Check availability first
        availability = check_availability(date_str, time_slot, property_id, db)
        
        if not availability.get("available"):
            return {
                "success": False,
                "reason": availability.get("reason"),
                "error": "Time slot not available"
            }
        
        # Create tour
        tour_id = str(uuid.uuid4())
        tour = {
            "id": tour_id,
            "lead_id": lead_id,
            "date": date_str,
            "time_slot": time_slot,
            "property_id": property_id,
            "notes": notes,
            "status": "scheduled",
            "created_at": datetime.utcnow().isoformat()
        }
        
        TOURS[tour_id] = tour
        
        # Log the activity
        activity = LeadActivity(
            lead_id=lead_id,
            activity_type="tour_scheduled",
            description=f"Tour scheduled for {date_str} at {time_slot}",
            metadata=tour
        )
        db.add(activity)
        db.commit()
        
        return {
            "success": True,
            "tour_id": tour_id,
            "lead_id": lead_id,
            "date": date_str,
            "time_slot": time_slot,
            "property_id": property_id,
            "message": f"Tour scheduled for {date_str} at {time_slot}"
        }
        
    except Exception as e:
        logger.error(f"Error scheduling tour: {str(e)}")
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }


def reschedule_tour(
    tour_id: str,
    new_date: str,
    new_time: str,
    db: Session,
    reason: str = None
) -> Dict[str, Any]:
    """
    Reschedule an existing tour.
    
    Args:
        tour_id: UUID of the tour
        new_date: New date in YYYY-MM-DD format
        new_time: New time slot
        db: Database session
        reason: Optional reason for rescheduling
    
    Returns:
        Dict with rescheduling result
    """
    try:
        if tour_id not in TOURS:
            return {
                "success": False,
                "error": f"Tour {tour_id} not found"
            }
        
        tour = TOURS[tour_id]
        
        # Check new availability
        availability = check_availability(
            new_date,
            new_time,
            tour.get("property_id"),
            db
        )
        
        if not availability.get("available"):
            return {
                "success": False,
                "reason": availability.get("reason"),
                "error": "New time slot not available"
            }
        
        # Update tour
        old_date = tour["date"]
        old_time = tour["time_slot"]
        
        tour["date"] = new_date
        tour["time_slot"] = new_time
        tour["updated_at"] = datetime.utcnow().isoformat()
        
        # Log the activity
        activity = LeadActivity(
            lead_id=tour["lead_id"],
            activity_type="tour_rescheduled",
            description=f"Tour rescheduled from {old_date} {old_time} to {new_date} {new_time}",
            metadata={
                "tour_id": tour_id,
                "old_date": old_date,
                "old_time": old_time,
                "new_date": new_date,
                "new_time": new_time,
                "reason": reason
            }
        )
        db.add(activity)
        db.commit()
        
        return {
            "success": True,
            "tour_id": tour_id,
            "old_date": old_date,
            "old_time": old_time,
            "new_date": new_date,
            "new_time": new_time,
            "message": f"Tour rescheduled to {new_date} at {new_time}"
        }
        
    except Exception as e:
        logger.error(f"Error rescheduling tour: {str(e)}")
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }


def cancel_tour(
    tour_id: str,
    db: Session,
    reason: str = None
) -> Dict[str, Any]:
    """
    Cancel a scheduled tour.
    
    Args:
        tour_id: UUID of the tour
        db: Database session
        reason: Optional reason for cancellation
    
    Returns:
        Dict with cancellation result
    """
    try:
        if tour_id not in TOURS:
            return {
                "success": False,
                "error": f"Tour {tour_id} not found"
            }
        
        tour = TOURS[tour_id]
        tour["status"] = "cancelled"
        tour["cancelled_at"] = datetime.utcnow().isoformat()
        tour["cancellation_reason"] = reason
        
        # Log the activity
        activity = LeadActivity(
            lead_id=tour["lead_id"],
            activity_type="tour_cancelled",
            description=f"Tour cancelled for {tour['date']} at {tour['time_slot']}",
            metadata={
                "tour_id": tour_id,
                "reason": reason,
                "date": tour["date"],
                "time_slot": tour["time_slot"]
            }
        )
        db.add(activity)
        db.commit()
        
        return {
            "success": True,
            "tour_id": tour_id,
            "message": "Tour cancelled successfully",
            "reason": reason
        }
        
    except Exception as e:
        logger.error(f"Error cancelling tour: {str(e)}")
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }

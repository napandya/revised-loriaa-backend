"""Communication tools for agents."""

from typing import Dict, Any
from sqlalchemy.orm import Session
import logging
from datetime import datetime

from app.models.lead_activity import LeadActivity
from app.core.config import settings

logger = logging.getLogger(__name__)


def send_sms(phone: str, message: str, lead_id: str = None, db: Session = None) -> Dict[str, Any]:
    """
    Send SMS message to a phone number.
    
    Args:
        phone: Phone number to send to
        message: Message content
        lead_id: Optional lead ID for tracking
        db: Optional database session for logging
    
    Returns:
        Dict with send result
    """
    try:
        # TODO: Integrate with Twilio
        # For now, simulate sending
        logger.info(f"SMS to {phone}: {message}")
        
        result = {
            "success": True,
            "phone": phone,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": f"sim_{datetime.utcnow().timestamp()}",
            "status": "sent"
        }
        
        # Log the interaction
        if db and lead_id:
            log_interaction(
                lead_id=lead_id,
                interaction_type="sms_sent",
                content=message,
                db=db
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Error sending SMS: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "phone": phone
        }


def send_email(
    email: str,
    subject: str,
    body: str,
    lead_id: str = None,
    db: Session = None
) -> Dict[str, Any]:
    """
    Send email message.
    
    Args:
        email: Email address to send to
        subject: Email subject
        body: Email body content
        lead_id: Optional lead ID for tracking
        db: Optional database session for logging
    
    Returns:
        Dict with send result
    """
    try:
        # TODO: Integrate with SendGrid
        # For now, simulate sending
        logger.info(f"Email to {email}: {subject}")
        
        result = {
            "success": True,
            "email": email,
            "subject": subject,
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": f"sim_{datetime.utcnow().timestamp()}",
            "status": "sent"
        }
        
        # Log the interaction
        if db and lead_id:
            log_interaction(
                lead_id=lead_id,
                interaction_type="email_sent",
                content=f"Subject: {subject}",
                db=db
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "email": email
        }


def log_interaction(
    lead_id: str,
    interaction_type: str,
    content: str,
    db: Session,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Log an interaction with a lead.
    
    Args:
        lead_id: UUID of the lead
        interaction_type: Type of interaction (sms, email, call, etc.)
        content: Interaction content summary
        db: Database session
        metadata: Optional additional metadata
    
    Returns:
        Dict with logging result
    """
    try:
        activity = LeadActivity(
            lead_id=lead_id,
            activity_type=interaction_type,
            description=content,
            metadata=metadata or {}
        )
        
        db.add(activity)
        db.commit()
        
        return {
            "success": True,
            "lead_id": lead_id,
            "interaction_type": interaction_type,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Interaction logged successfully"
        }
        
    except Exception as e:
        logger.error(f"Error logging interaction: {str(e)}")
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }

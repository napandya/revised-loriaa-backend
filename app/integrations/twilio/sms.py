"""Twilio SMS handling."""

from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.integrations.twilio.client import TwilioClient
from app.core.exceptions import IntegrationError


async def send_lead_sms(
    lead_id: str,
    message: str,
    db: AsyncSession,
    media_urls: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Send SMS to a lead.
    
    Args:
        lead_id: Lead UUID
        message: Message text
        db: Database session
        media_urls: Optional list of media URLs for MMS
        
    Returns:
        Message send response
        
    Raises:
        IntegrationError: If lead not found or has no phone
    """
    from app.models.lead import Lead
    from sqlalchemy import select
    
    # Get lead
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id)
    )
    lead = result.scalar_one_or_none()
    
    if not lead:
        raise IntegrationError(
            message=f"Lead not found: {lead_id}",
            integration_name="twilio",
            details={"lead_id": lead_id}
        )
    
    if not lead.phone:
        raise IntegrationError(
            message=f"Lead has no phone number",
            integration_name="twilio",
            details={"lead_id": lead_id}
        )
    
    client = TwilioClient()
    
    return await client.send_sms(
        to=lead.phone,
        body=message,
        media_url=media_urls
    )


async def send_bulk_sms(
    phone_numbers: List[str],
    message: str,
    media_urls: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Send SMS to multiple phone numbers.
    
    Args:
        phone_numbers: List of phone numbers (E.164 format)
        message: Message text
        media_urls: Optional list of media URLs for MMS
        
    Returns:
        Summary of sent messages
    """
    client = TwilioClient()
    
    results = {
        "total": len(phone_numbers),
        "sent": 0,
        "failed": 0,
        "messages": []
    }
    
    for phone in phone_numbers:
        try:
            response = await client.send_sms(
                to=phone,
                body=message,
                media_url=media_urls
            )
            results["sent"] += 1
            results["messages"].append({
                "phone": phone,
                "status": "sent",
                "sid": response.get("sid")
            })
        except Exception as e:
            results["failed"] += 1
            results["messages"].append({
                "phone": phone,
                "status": "failed",
                "error": str(e)
            })
    
    return results


def format_message_for_sms(
    template: str,
    variables: Dict[str, Any]
) -> str:
    """Format a message template with variables.
    
    Args:
        template: Message template with {variable} placeholders
        variables: Dictionary of variable values
        
    Returns:
        Formatted message
        
    Example:
        template = "Hi {name}, your tour is scheduled for {date} at {time}."
        variables = {"name": "John", "date": "2024-01-15", "time": "2:00 PM"}
        result = "Hi John, your tour is scheduled for 2024-01-15 at 2:00 PM."
    """
    try:
        return template.format(**variables)
    except KeyError as e:
        raise IntegrationError(
            message=f"Missing template variable: {str(e)}",
            integration_name="twilio",
            details={"template": template, "variables": list(variables.keys())}
        )


async def send_templated_sms(
    to: str,
    template: str,
    variables: Dict[str, Any],
    media_urls: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Send SMS using a template.
    
    Args:
        to: Recipient phone number
        template: Message template
        variables: Template variables
        media_urls: Optional media URLs
        
    Returns:
        Message send response
    """
    message = format_message_for_sms(template, variables)
    
    client = TwilioClient()
    return await client.send_sms(
        to=to,
        body=message,
        media_url=media_urls
    )


async def get_lead_sms_history(
    lead_id: str,
    db: AsyncSession,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Get SMS history for a lead.
    
    Args:
        lead_id: Lead UUID
        db: Database session
        limit: Maximum number of messages
        
    Returns:
        List of SMS messages
    """
    from app.models.lead import Lead
    from sqlalchemy import select
    
    # Get lead
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id)
    )
    lead = result.scalar_one_or_none()
    
    if not lead or not lead.phone:
        return []
    
    client = TwilioClient()
    return await client.get_conversation_history(lead.phone, limit)


# Common SMS templates
SMS_TEMPLATES = {
    "welcome": "Hi {name}! Thanks for your interest in {property_name}. I'm here to help answer any questions. Reply anytime!",
    "tour_scheduled": "Hi {name}! Your tour at {property_name} is confirmed for {date} at {time}. See you then!",
    "tour_reminder": "Reminder: Your tour at {property_name} is tomorrow at {time}. Reply CONFIRM or call us at {phone}.",
    "follow_up": "Hi {name}! Just checking in after your tour of {property_name}. Do you have any questions?",
    "application_received": "Great news {name}! We received your application for {property_name}. We'll review it and get back to you soon.",
    "lease_ready": "Hi {name}! Your lease for {property_name} is ready. Please visit our office to sign. Congrats!"
}

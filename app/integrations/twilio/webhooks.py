"""Twilio webhook handlers for incoming SMS."""

from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.lead import Lead, LeadSource, LeadStatus
from app.models.message import Message
from app.core.exceptions import IntegrationError
import hashlib
import hmac
from urllib.parse import urljoin


def verify_twilio_signature(
    url: str,
    params: Dict[str, str],
    signature: str
) -> bool:
    """Verify Twilio webhook signature.
    
    Args:
        url: Full URL of the webhook endpoint
        params: POST parameters from Twilio
        signature: X-Twilio-Signature header value
        
    Returns:
        True if signature is valid, False otherwise
    """
    from app.core.config import settings
    
    auth_token = settings.TWILIO_AUTH_TOKEN
    
    if not auth_token:
        raise IntegrationError(
            message="Twilio auth token not configured",
            integration_name="twilio"
        )
    
    # Create the signature string
    data = url
    for key in sorted(params.keys()):
        data += key + params[key]
    
    # Compute HMAC-SHA1
    mac = hmac.new(
        auth_token.encode(),
        data.encode(),
        hashlib.sha1
    )
    expected_signature = mac.digest().hex()
    
    # Compare signatures
    return hmac.compare_digest(expected_signature, signature)


async def process_incoming_sms(
    from_number: str,
    body: str,
    db: AsyncSession,
    message_sid: Optional[str] = None,
    media_urls: Optional[list] = None,
    num_media: int = 0
) -> Dict[str, Any]:
    """Process incoming SMS message.
    
    Args:
        from_number: Sender phone number
        body: Message body
        db: Database session
        message_sid: Twilio message SID
        media_urls: List of media URLs if MMS
        num_media: Number of media items
        
    Returns:
        Processing result with response message
    """
    # Find or create lead by phone
    lead = await find_or_create_lead_by_phone(from_number, db)
    
    # Save message to database
    message = await save_incoming_message(
        lead_id=str(lead.id),
        from_number=from_number,
        body=body,
        db=db,
        message_sid=message_sid,
        media_urls=media_urls
    )
    
    # Determine if auto-reply should be sent
    should_reply = await should_send_auto_reply(lead, db)
    
    response = {
        "lead_id": str(lead.id),
        "message_id": str(message.id),
        "auto_reply": None
    }
    
    if should_reply:
        reply_message = get_auto_reply_message(body, lead)
        response["auto_reply"] = reply_message
    
    return response


async def find_or_create_lead_by_phone(
    phone: str,
    db: AsyncSession,
    property_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> Lead:
    """Find existing lead or create new one by phone number.
    
    Args:
        phone: Phone number
        db: Database session
        property_id: Optional property ID for new leads
        user_id: Optional user ID for new leads
        
    Returns:
        Lead object
    """
    # Try to find existing lead
    result = await db.execute(
        select(Lead).where(Lead.phone == phone)
    )
    lead = result.scalar_one_or_none()
    
    if lead:
        return lead
    
    # Create new lead
    lead = Lead(
        name=f"SMS Lead {phone}",
        phone=phone,
        source=LeadSource.phone,
        status=LeadStatus.new,
        score=30,  # Default score for SMS leads
        property_id=property_id,
        user_id=user_id,
        metadata={"created_from": "sms"}
    )
    
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    
    return lead


async def save_incoming_message(
    lead_id: str,
    from_number: str,
    body: str,
    db: AsyncSession,
    message_sid: Optional[str] = None,
    media_urls: Optional[list] = None
) -> Message:
    """Save incoming message to database.
    
    Args:
        lead_id: Lead UUID
        from_number: Sender phone number
        body: Message body
        db: Database session
        message_sid: Twilio message SID
        media_urls: Media URLs if MMS
        
    Returns:
        Created Message object
    """
    message = Message(
        lead_id=lead_id,
        direction="inbound",
        channel="sms",
        from_number=from_number,
        body=body,
        metadata={
            "twilio_message_sid": message_sid,
            "media_urls": media_urls or []
        }
    )
    
    db.add(message)
    await db.commit()
    await db.refresh(message)
    
    return message


async def should_send_auto_reply(lead: Lead, db: AsyncSession) -> bool:
    """Determine if auto-reply should be sent.
    
    Args:
        lead: Lead object
        db: Database session
        
    Returns:
        True if auto-reply should be sent
    """
    # Don't auto-reply to leads already in conversation
    if lead.status in [LeadStatus.contacted, LeadStatus.qualified]:
        return False
    
    # Check if we've already sent auto-reply recently
    from app.models.message import Message
    from sqlalchemy import desc
    from datetime import datetime, timedelta
    
    recent_cutoff = datetime.utcnow() - timedelta(hours=24)
    
    result = await db.execute(
        select(Message)
        .where(
            Message.lead_id == lead.id,
            Message.direction == "outbound",
            Message.channel == "sms",
            Message.created_at > recent_cutoff
        )
        .order_by(desc(Message.created_at))
        .limit(1)
    )
    
    recent_outbound = result.scalar_one_or_none()
    
    # Send auto-reply if no recent outbound message
    return recent_outbound is None


def get_auto_reply_message(incoming_message: str, lead: Lead) -> str:
    """Generate auto-reply message based on incoming message.
    
    Args:
        incoming_message: The incoming SMS body
        body: Message body
        lead: Lead object
        
    Returns:
        Auto-reply message text
    """
    message_lower = incoming_message.lower()
    
    # Check for keywords
    if any(word in message_lower for word in ["tour", "visit", "see"]):
        return f"Hi! Thanks for reaching out. I'd love to schedule a tour for you. What day works best? Reply with a date or call us!"
    
    if any(word in message_lower for word in ["price", "cost", "rent", "$"]):
        return "Great question! Our pricing varies by unit. I can provide specific rates when we know your move-in date and preferences. Want to schedule a call?"
    
    if any(word in message_lower for word in ["available", "vacancy", "unit"]):
        return "We have units available! What size are you looking for and when do you need to move in? I can check availability for you."
    
    if any(word in message_lower for word in ["apply", "application"]):
        return "Wonderful! I can help you with the application process. Have you toured the property yet? That's usually the first step."
    
    # Default auto-reply
    return f"Hi! Thanks for contacting us. I'm here to help answer questions about the property. Feel free to ask anything or let me know if you'd like to schedule a tour!"


async def send_twiml_response(message: str) -> str:
    """Generate TwiML response for Twilio webhook.
    
    Args:
        message: Response message to send
        
    Returns:
        TwiML XML string
    """
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{message}</Message>
</Response>"""

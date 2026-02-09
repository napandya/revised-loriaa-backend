"""Twilio integration API endpoints for SMS."""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, Form, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.integrations.twilio.client import TwilioClient

router = APIRouter(prefix="/integrations/twilio", tags=["integrations", "twilio"])


@router.post("/sms/send")
async def send_sms(
    to_number: str,
    message: str,
    from_number: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send SMS via Twilio."""
    try:
        client = TwilioClient(db=db, user_id=current_user.id)
        result = client.send_sms(
            to_number=to_number,
            message=message,
            from_number=from_number
        )
        return {"status": "success", "message_sid": result.sid}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send SMS: {str(e)}"
        )


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def twilio_sms_webhook(
    MessageSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    Body: str = Form(...),
    NumMedia: str = Form("0"),
    MediaUrl0: Optional[str] = Form(None),
    FromCity: Optional[str] = Form(None),
    FromState: Optional[str] = Form(None),
    FromZip: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Twilio incoming SMS webhook (no auth required)."""
    try:
        from app.services.inbox_service import process_incoming_sms
        
        webhook_data = {
            "MessageSid": MessageSid,
            "From": From,
            "To": To,
            "Body": Body,
            "NumMedia": NumMedia,
            "MediaUrl0": MediaUrl0,
            "FromCity": FromCity,
            "FromState": FromState,
            "FromZip": FromZip,
        }
        
        result = process_incoming_sms(db=db, webhook_data=webhook_data)
        
        return {"status": "success", "conversation_id": str(result.get("conversation_id"))}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}"
        )


@router.get("/messages/{lead_id}")
async def get_message_history(
    lead_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get SMS message history for a lead."""
    try:
        from app.services.inbox_service import get_lead_messages
        
        messages = get_lead_messages(db=db, lead_id=lead_id)
        return {"lead_id": str(lead_id), "messages": messages}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch messages: {str(e)}"
        )

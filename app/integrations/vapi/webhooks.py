"""Vapi webhook handlers for call events and function calling."""

import hmac
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.exceptions import VoiceError
from app.models.call_log import CallLog, CallType, CallStatus
from app.models.lead_activity import LeadActivity, ActivityType
from app.models.lead import Lead, LeadStatus
from app.models.bot import Bot


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify Vapi webhook signature.
    
    Args:
        payload: Raw webhook payload bytes
        signature: Signature from webhook header
        
    Returns:
        True if signature is valid, False otherwise
    """
    if not settings.VAPI_WEBHOOK_SECRET:
        # If no secret configured, skip verification (for testing)
        return True
    
    expected_signature = hmac.new(
        settings.VAPI_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)


async def handle_webhook(
    event_type: str,
    payload: Dict[str, Any],
    db: Session
) -> Dict[str, Any]:
    """Main webhook handler that routes to specific event handlers.
    
    Args:
        event_type: Type of webhook event
        payload: Webhook payload data
        db: Database session
        
    Returns:
        Response data
        
    Raises:
        VoiceError: If webhook handling fails
    """
    handlers = {
        "call.started": on_call_started,
        "call.ended": on_call_ended,
        "function-call": on_function_call,
        "transcript": on_transcript_update,
        "status-update": on_status_update
    }
    
    handler = handlers.get(event_type)
    if not handler:
        return {"status": "ignored", "message": f"No handler for event: {event_type}"}
    
    try:
        return await handler(payload, db)
    except Exception as e:
        raise VoiceError(
            message=f"Webhook handler failed for {event_type}: {str(e)}",
            details={"event_type": event_type, "error": str(e)}
        )


async def on_call_started(call_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Handle call started event.
    
    Args:
        call_data: Call data from webhook
        db: Database session
        
    Returns:
        Success response
    """
    call_id = call_data.get("call", {}).get("id")
    assistant_id = call_data.get("call", {}).get("assistantId")
    customer_number = call_data.get("call", {}).get("customer", {}).get("number")
    
    # Find bot by assistant_id (stored in bot metadata or phone_number)
    bot = db.query(Bot).filter(Bot.phone_number.contains(assistant_id)).first()
    
    if bot:
        # Create initial call log
        call_log = CallLog(
            id=call_id,
            bot_id=bot.id,
            bot_name=bot.name,
            start_time=datetime.utcnow(),
            phone_number=customer_number or "Unknown",
            call_type=CallType.outbound if call_data.get("call", {}).get("type") == "outbound" else CallType.inbound,
            status=CallStatus.in_progress
        )
        db.add(call_log)
        db.commit()
    
    return {"status": "success", "message": "Call started logged"}


async def on_call_ended(call_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Handle call ended event and save to database.
    
    Args:
        call_data: Call data from webhook
        db: Database session
        
    Returns:
        Success response
    """
    call = call_data.get("call", {})
    call_id = call.get("id")
    assistant_id = call.get("assistantId")
    customer_number = call.get("customer", {}).get("number")
    duration = call.get("duration", 0)
    status = call.get("status", "completed")
    transcript_data = call.get("transcript", [])
    recording_url = call.get("recordingUrl")
    
    # Build transcript text
    transcript = ""
    if transcript_data:
        transcript = "\n".join([
            f"{msg.get('role', 'unknown')}: {msg.get('message', '')}"
            for msg in transcript_data
        ])
    
    # Find bot by assistant_id
    bot = db.query(Bot).filter(Bot.phone_number.contains(assistant_id)).first()
    
    if not bot:
        return {"status": "error", "message": "Bot not found for assistant"}
    
    # Check if call log exists, update or create
    call_log = db.query(CallLog).filter(CallLog.id == call_id).first()
    
    if call_log:
        call_log.duration_seconds = duration
        call_log.status = CallStatus.completed if status == "ended" else CallStatus.failed
        call_log.transcript = transcript
        call_log.recording_url = recording_url
    else:
        call_log = CallLog(
            id=call_id,
            bot_id=bot.id,
            bot_name=bot.name,
            start_time=datetime.utcnow(),
            phone_number=customer_number or "Unknown",
            call_type=CallType.outbound if call.get("type") == "outbound" else CallType.inbound,
            duration_seconds=duration,
            status=CallStatus.completed if status == "ended" else CallStatus.failed,
            transcript=transcript,
            recording_url=recording_url
        )
        db.add(call_log)
    
    # Try to find associated lead by phone number
    lead = db.query(Lead).filter(
        Lead.phone == customer_number,
        Lead.property_id == bot.id
    ).first()
    
    if lead:
        # Create lead activity for the call
        activity = LeadActivity(
            lead_id=lead.id,
            user_id=bot.user_id,
            activity_type=ActivityType.call,
            description=f"Call ended - Duration: {duration}s",
            metadata={
                "call_id": call_id,
                "duration": duration,
                "status": status,
                "transcript_preview": transcript[:200] if transcript else None
            }
        )
        db.add(activity)
    
    db.commit()
    
    return {"status": "success", "message": "Call ended and saved"}


async def on_function_call(
    function_data: Dict[str, Any],
    db: Session
) -> Dict[str, Any]:
    """Handle function call from Vapi assistant.
    
    Args:
        function_data: Function call data
        db: Database session
        
    Returns:
        Function execution result
    """
    function_name = function_data.get("functionCall", {}).get("name")
    parameters = function_data.get("functionCall", {}).get("parameters", {})
    call_id = function_data.get("call", {}).get("id")
    
    # Route to appropriate function handler
    if function_name == "check_availability":
        return await check_availability(parameters, db)
    elif function_name == "schedule_tour":
        return await schedule_tour(parameters, call_id, db)
    elif function_name == "qualify_lead":
        return await qualify_lead(parameters, call_id, db)
    elif function_name == "transfer_to_human":
        return await transfer_to_human(parameters, call_id, db)
    else:
        return {
            "status": "error",
            "message": f"Unknown function: {function_name}"
        }


async def check_availability(
    parameters: Dict[str, Any],
    db: Session
) -> Dict[str, Any]:
    """Check unit availability for given criteria.
    
    Args:
        parameters: Function parameters (property_id, bedrooms, move_in_date)
        db: Database session
        
    Returns:
        Availability information
    """
    property_id = parameters.get("property_id")
    bedrooms = parameters.get("bedrooms")
    move_in_date = parameters.get("move_in_date")
    
    # TODO: Integrate with PMS system for real availability
    # For now, return mock data
    return {
        "status": "success",
        "result": {
            "available": True,
            "units": [
                {
                    "unit_number": "101",
                    "bedrooms": bedrooms,
                    "rent": 1500,
                    "available_date": move_in_date
                }
            ],
            "message": f"We have {bedrooms}-bedroom units available starting {move_in_date}"
        }
    }


async def schedule_tour(
    parameters: Dict[str, Any],
    call_id: str,
    db: Session
) -> Dict[str, Any]:
    """Schedule a property tour.
    
    Args:
        parameters: Function parameters (property_id, lead_name, lead_phone, preferred_date)
        call_id: Current call ID
        db: Database session
        
    Returns:
        Tour scheduling confirmation
    """
    property_id = parameters.get("property_id")
    lead_name = parameters.get("lead_name")
    lead_phone = parameters.get("lead_phone")
    preferred_date = parameters.get("preferred_date")
    
    # Find or create lead
    lead = db.query(Lead).filter(
        Lead.phone == lead_phone,
        Lead.property_id == property_id
    ).first()
    
    if not lead:
        bot = db.query(Bot).filter(Bot.id == property_id).first()
        if bot:
            lead = Lead(
                property_id=property_id,
                user_id=bot.user_id,
                name=lead_name,
                phone=lead_phone,
                source="phone",
                status=LeadStatus.new
            )
            db.add(lead)
            db.flush()
    
    if lead:
        # Update lead status
        lead.status = LeadStatus.touring
        
        # Create activity
        activity = LeadActivity(
            lead_id=lead.id,
            user_id=lead.user_id,
            activity_type=ActivityType.tour_scheduled,
            description=f"Tour scheduled for {preferred_date}",
            metadata={
                "call_id": call_id,
                "preferred_date": preferred_date
            }
        )
        db.add(activity)
        db.commit()
    
    return {
        "status": "success",
        "result": {
            "scheduled": True,
            "date": preferred_date,
            "message": f"Tour scheduled for {preferred_date}. We'll send a confirmation text to {lead_phone}"
        }
    }


async def qualify_lead(
    parameters: Dict[str, Any],
    call_id: str,
    db: Session
) -> Dict[str, Any]:
    """Qualify a lead based on their responses.
    
    Args:
        parameters: Function parameters (budget, move_in_timeline, bedrooms)
        call_id: Current call ID
        db: Database session
        
    Returns:
        Lead qualification result
    """
    budget = parameters.get("budget")
    move_in_timeline = parameters.get("move_in_timeline")
    bedrooms = parameters.get("bedrooms")
    
    # Calculate lead score based on criteria
    score = 0
    
    if budget and budget >= 1000:
        score += 30
    if move_in_timeline in ["immediately", "1-2 weeks"]:
        score += 40
    if bedrooms:
        score += 30
    
    qualification = "high" if score >= 70 else "medium" if score >= 40 else "low"
    
    # Find call log and update lead if exists
    call_log = db.query(CallLog).filter(CallLog.id == call_id).first()
    if call_log:
        lead = db.query(Lead).filter(
            Lead.property_id == call_log.bot_id
        ).first()
        
        if lead:
            lead.score = score
            lead.status = LeadStatus.qualified if score >= 70 else lead.status
            lead.extra_data = lead.extra_data or {}
            lead.extra_data.update({
                "budget": budget,
                "move_in_timeline": move_in_timeline,
                "bedrooms": bedrooms,
                "qualification": qualification
            })
            db.commit()
    
    return {
        "status": "success",
        "result": {
            "qualified": qualification,
            "score": score,
            "message": f"Lead qualified as {qualification} priority"
        }
    }


async def transfer_to_human(
    parameters: Dict[str, Any],
    call_id: str,
    db: Session
) -> Dict[str, Any]:
    """Handle transfer to human agent.
    
    Args:
        parameters: Function parameters (reason)
        call_id: Current call ID
        db: Database session
        
    Returns:
        Transfer instruction
    """
    reason = parameters.get("reason", "Customer requested")
    
    # Log the transfer request
    call_log = db.query(CallLog).filter(CallLog.id == call_id).first()
    if call_log:
        lead = db.query(Lead).filter(
            Lead.property_id == call_log.bot_id
        ).first()
        
        if lead:
            activity = LeadActivity(
                lead_id=lead.id,
                user_id=lead.user_id,
                activity_type=ActivityType.note,
                description=f"Transfer to human requested: {reason}",
                metadata={
                    "call_id": call_id,
                    "reason": reason
                }
            )
            db.add(activity)
            db.commit()
    
    return {
        "status": "success",
        "result": {
            "transfer": True,
            "message": "Transferring you to a leasing agent now. Please hold."
        }
    }


async def on_transcript_update(
    transcript_data: Dict[str, Any],
    db: Session
) -> Dict[str, Any]:
    """Handle real-time transcript updates.
    
    Args:
        transcript_data: Transcript data from webhook
        db: Database session
        
    Returns:
        Success response
    """
    # For now, just acknowledge receipt
    # Could be used for real-time monitoring or analytics
    return {"status": "success", "message": "Transcript update received"}


async def on_status_update(
    status_data: Dict[str, Any],
    db: Session
) -> Dict[str, Any]:
    """Handle call status updates.
    
    Args:
        status_data: Status data from webhook
        db: Database session
        
    Returns:
        Success response
    """
    call_id = status_data.get("call", {}).get("id")
    status = status_data.get("status")
    
    # Update call log status if it exists
    call_log = db.query(CallLog).filter(CallLog.id == call_id).first()
    if call_log:
        if status == "ringing":
            call_log.status = CallStatus.in_progress
        elif status in ["ended", "completed"]:
            call_log.status = CallStatus.completed
        elif status == "failed":
            call_log.status = CallStatus.failed
        
        db.commit()
    
    return {"status": "success", "message": "Status update processed"}

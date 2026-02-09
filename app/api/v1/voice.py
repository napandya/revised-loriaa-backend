"""Voice API endpoints for Vapi integration."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.bot import Bot
from app.models.call_log import CallLog
from app.models.lead import Lead
from app.api.deps import get_current_user
from app.core.exceptions import VoiceError, NotFoundError
from app.integrations.vapi.client import vapi_client
from app.integrations.vapi.assistants import (
    create_property_assistant,
    configure_assistant_functions,
    update_assistant_knowledge,
    test_assistant
)
from app.integrations.vapi.webhooks import handle_webhook, verify_webhook_signature
from app.schemas.voice import (
    VapiAssistantConfig,
    VapiCallRequest,
    VapiCallResponse,
    VapiCallDetails
)

router = APIRouter()


@router.post("/assistants", status_code=status.HTTP_201_CREATED)
async def create_assistant(
    property_id: UUID,
    config: VapiAssistantConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a Vapi assistant for a property.
    
    Args:
        property_id: Property/bot ID
        config: Assistant configuration
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Created assistant details
        
    Raises:
        NotFoundError: If property not found
        VoiceError: If assistant creation fails
    """
    # Verify property belongs to user
    bot = db.query(Bot).filter(
        Bot.id == property_id,
        Bot.user_id == current_user.id
    ).first()
    
    if not bot:
        raise NotFoundError(
            message=f"Property {property_id} not found",
            resource_type="Property"
        )
    
    try:
        # Create assistant
        assistant = await create_property_assistant(
            property_id=str(property_id),
            property_name=config.name or bot.name,
            system_prompt=config.system_prompt,
            first_message=config.first_message,
            voice_id=config.voice_id
        )
        
        # Store assistant_id in bot's phone_number field (temporary)
        # In production, you'd have a separate assistant_id column
        bot.phone_number = assistant.get("id", "")
        db.commit()
        
        return {
            "assistant_id": assistant.get("id"),
            "property_id": str(property_id),
            "name": config.name or bot.name,
            "status": "active",
            "created_at": datetime.utcnow()
        }
        
    except Exception as e:
        raise VoiceError(
            message=f"Failed to create assistant: {str(e)}",
            details={"property_id": str(property_id)}
        )


@router.get("/assistants/{assistant_id}")
async def get_assistant(
    assistant_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get assistant details.
    
    Args:
        assistant_id: Assistant ID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Assistant details
        
    Raises:
        NotFoundError: If assistant not found
    """
    # Verify assistant belongs to user's property
    bot = db.query(Bot).filter(
        Bot.phone_number == assistant_id,
        Bot.user_id == current_user.id
    ).first()
    
    if not bot:
        raise NotFoundError(
            message=f"Assistant {assistant_id} not found",
            resource_type="Assistant"
        )
    
    try:
        assistant = await vapi_client.get_assistant(assistant_id)
        return {
            "assistant_id": assistant_id,
            "property_id": str(bot.id),
            "name": assistant.get("name"),
            "configuration": assistant
        }
    except Exception as e:
        raise VoiceError(
            message=f"Failed to get assistant: {str(e)}",
            details={"assistant_id": assistant_id}
        )


@router.put("/assistants/{assistant_id}")
async def update_assistant(
    assistant_id: str,
    config: VapiAssistantConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update assistant configuration.
    
    Args:
        assistant_id: Assistant ID
        config: New assistant configuration
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Updated assistant details
        
    Raises:
        NotFoundError: If assistant not found
    """
    # Verify assistant belongs to user's property
    bot = db.query(Bot).filter(
        Bot.phone_number == assistant_id,
        Bot.user_id == current_user.id
    ).first()
    
    if not bot:
        raise NotFoundError(
            message=f"Assistant {assistant_id} not found",
            resource_type="Assistant"
        )
    
    try:
        assistant = await vapi_client.update_assistant(
            assistant_id=assistant_id,
            name=config.name,
            first_message=config.first_message,
            system_prompt=config.system_prompt,
            voice_id=config.voice_id,
            model=config.model,
            functions=config.functions
        )
        
        return {
            "assistant_id": assistant_id,
            "property_id": str(bot.id),
            "status": "updated",
            "configuration": assistant
        }
    except Exception as e:
        raise VoiceError(
            message=f"Failed to update assistant: {str(e)}",
            details={"assistant_id": assistant_id}
        )


@router.delete("/assistants/{assistant_id}")
async def delete_assistant(
    assistant_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an assistant.
    
    Args:
        assistant_id: Assistant ID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Deletion confirmation
        
    Raises:
        NotFoundError: If assistant not found
    """
    # Verify assistant belongs to user's property
    bot = db.query(Bot).filter(
        Bot.phone_number == assistant_id,
        Bot.user_id == current_user.id
    ).first()
    
    if not bot:
        raise NotFoundError(
            message=f"Assistant {assistant_id} not found",
            resource_type="Assistant"
        )
    
    try:
        await vapi_client.delete_assistant(assistant_id)
        
        # Clear assistant_id from bot
        bot.phone_number = None
        db.commit()
        
        return {
            "assistant_id": assistant_id,
            "status": "deleted",
            "message": "Assistant deleted successfully"
        }
    except Exception as e:
        raise VoiceError(
            message=f"Failed to delete assistant: {str(e)}",
            details={"assistant_id": assistant_id}
        )


@router.post("/call", response_model=VapiCallResponse)
async def make_call(
    call_request: VapiCallRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Make an outbound call using Vapi.
    
    Args:
        call_request: Call request details
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Call initiation response
        
    Raises:
        NotFoundError: If assistant not found
    """
    # Verify assistant belongs to user
    bot = db.query(Bot).filter(
        Bot.phone_number == call_request.assistant_id,
        Bot.user_id == current_user.id
    ).first()
    
    if not bot:
        raise NotFoundError(
            message=f"Assistant {call_request.assistant_id} not found",
            resource_type="Assistant"
        )
    
    # Get lead info if lead_id provided
    customer_name = None
    if call_request.lead_id:
        lead = db.query(Lead).filter(Lead.id == call_request.lead_id).first()
        if lead:
            customer_name = lead.name
    
    try:
        # Make outbound call via Vapi
        call_result = await vapi_client.make_outbound_call(
            assistant_id=call_request.assistant_id,
            customer_number=call_request.phone_number,
            customer_name=customer_name,
            metadata=call_request.metadata
        )
        
        return VapiCallResponse(
            call_id=call_result.get("id", ""),
            status=call_result.get("status", "initiated"),
            message="Call initiated successfully",
            started_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise VoiceError(
            message=f"Failed to initiate call: {str(e)}",
            details={
                "assistant_id": call_request.assistant_id,
                "phone_number": call_request.phone_number
            }
        )


@router.get("/calls", response_model=List[VapiCallDetails])
async def list_calls(
    assistant_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List calls with optional filtering.
    
    Args:
        assistant_id: Optional filter by assistant ID
        limit: Maximum number of calls to return
        offset: Number of calls to skip
        current_user: Authenticated user
        db: Database session
        
    Returns:
        List of calls
    """
    # Get user's bots
    user_bots = db.query(Bot).filter(Bot.user_id == current_user.id).all()
    user_bot_ids = [str(bot.id) for bot in user_bots]
    
    # Query call logs
    query = db.query(CallLog).filter(CallLog.bot_id.in_(user_bot_ids))
    
    if assistant_id:
        # Filter by assistant_id (stored in phone_number temporarily)
        bot = db.query(Bot).filter(
            Bot.phone_number == assistant_id,
            Bot.user_id == current_user.id
        ).first()
        if bot:
            query = query.filter(CallLog.bot_id == bot.id)
    
    # Apply pagination
    calls = query.order_by(CallLog.created_at.desc()).offset(offset).limit(limit).all()
    
    # Convert to response format
    result = []
    for call in calls:
        result.append(
            VapiCallDetails(
                call_id=str(call.id),
                status=call.status.value,
                duration_seconds=call.duration_seconds,
                cost=None,  # Calculate based on duration if needed
                transcription=[],  # Parse transcript if needed
                summary=call.transcript[:200] if call.transcript else None,
                sentiment=None,  # Add sentiment analysis if needed
                created_at=call.created_at,
                ended_at=None  # Calculate from start_time + duration if needed
            )
        )
    
    return result


@router.get("/calls/{call_id}", response_model=VapiCallDetails)
async def get_call(
    call_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get details of a specific call.
    
    Args:
        call_id: Call ID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Call details
        
    Raises:
        NotFoundError: If call not found
    """
    # Get call log from database
    call_log = db.query(CallLog).filter(CallLog.id == call_id).first()
    
    if not call_log:
        raise NotFoundError(
            message=f"Call {call_id} not found",
            resource_type="Call"
        )
    
    # Verify call belongs to user's bot
    bot = db.query(Bot).filter(
        Bot.id == call_log.bot_id,
        Bot.user_id == current_user.id
    ).first()
    
    if not bot:
        raise NotFoundError(
            message=f"Call {call_id} not found",
            resource_type="Call"
        )
    
    # Try to get additional details from Vapi
    try:
        vapi_call = await vapi_client.get_call(call_id)
        
        # Parse transcript
        transcription = []
        if vapi_call.get("transcript"):
            for msg in vapi_call["transcript"]:
                transcription.append({
                    "speaker": msg.get("role", "unknown"),
                    "text": msg.get("message", ""),
                    "timestamp": msg.get("timestamp", datetime.utcnow())
                })
        
        return VapiCallDetails(
            call_id=call_id,
            status=vapi_call.get("status", call_log.status.value),
            duration_seconds=vapi_call.get("duration", call_log.duration_seconds),
            cost=vapi_call.get("cost"),
            transcription=transcription,
            summary=vapi_call.get("summary", call_log.transcript[:200] if call_log.transcript else None),
            sentiment=vapi_call.get("sentiment"),
            created_at=call_log.created_at,
            ended_at=vapi_call.get("endedAt")
        )
        
    except Exception:
        # Fallback to database data if Vapi call fails
        return VapiCallDetails(
            call_id=call_id,
            status=call_log.status.value,
            duration_seconds=call_log.duration_seconds,
            cost=None,
            transcription=[],
            summary=call_log.transcript[:200] if call_log.transcript else None,
            sentiment=None,
            created_at=call_log.created_at,
            ended_at=None
        )


@router.post("/webhook", include_in_schema=False)
async def vapi_webhook(
    request: Request,
    x_vapi_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Webhook endpoint for Vapi events (no authentication required).
    
    Args:
        request: FastAPI request object
        x_vapi_signature: Vapi webhook signature header
        db: Database session
        
    Returns:
        Webhook processing result
        
    Raises:
        HTTPException: If signature verification fails
    """
    # Get raw body for signature verification
    body = await request.body()
    
    # Verify webhook signature
    if x_vapi_signature and not verify_webhook_signature(body, x_vapi_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature"
        )
    
    # Parse JSON payload
    try:
        payload = await request.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON payload: {str(e)}"
        )
    
    # Get event type
    event_type = payload.get("type") or payload.get("event_type")
    
    if not event_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing event type in webhook payload"
        )
    
    # Handle webhook
    try:
        result = await handle_webhook(event_type, payload, db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}"
        )

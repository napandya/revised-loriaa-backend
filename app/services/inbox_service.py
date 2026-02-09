"""Unified inbox service for multi-channel message aggregation."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.models.conversation import Conversation, ConversationChannel, ConversationStatus
from app.models.message import Message, MessageDirection
from app.models.lead import Lead
from app.core.exceptions import NotFoundError, DatabaseError


async def get_unified_inbox(
    db: Session,
    user_id: Optional[UUID] = None,
    property_id: Optional[UUID] = None,
    channel: Optional[ConversationChannel] = None,
    status: Optional[ConversationStatus] = None,
    skip: int = 0,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Get unified inbox aggregating messages from all channels.
    
    Aggregates messages from:
    - SMS
    - Email
    - Voice
    - Chat
    
    Args:
        db: Database session
        user_id: Filter by user (property manager)
        property_id: Filter by property
        channel: Filter by specific channel
        status: Filter by conversation status
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        Dictionary with conversations list and metadata
    """
    try:
        # Build query with joins
        query = db.query(Conversation).join(Lead)
        
        # Apply filters
        if user_id:
            query = query.filter(Lead.user_id == user_id)
        if property_id:
            query = query.filter(Lead.property_id == property_id)
        if channel:
            query = query.filter(Conversation.channel == channel)
        if status:
            query = query.filter(Conversation.status == status)
        
        # Order by most recent message
        query = query.order_by(desc(Conversation.last_message_at))
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        conversations = query.offset(skip).limit(limit).all()
        
        # Build response with enriched data
        inbox_items = []
        for conv in conversations:
            # Get last message
            last_message = db.query(Message).filter(
                Message.conversation_id == conv.id
            ).order_by(desc(Message.created_at)).first()
            
            # Count unread messages (assuming inbound messages not in metadata are unread)
            unread_count = db.query(Message).filter(
                and_(
                    Message.conversation_id == conv.id,
                    Message.direction == MessageDirection.inbound
                )
            ).count()
            
            inbox_items.append({
                "id": str(conv.id),
                "lead_id": str(conv.lead_id),
                "lead_name": conv.lead.name if conv.lead else "Unknown",
                "lead_phone": conv.lead.phone if conv.lead else None,
                "lead_email": conv.lead.email if conv.lead else None,
                "channel": conv.channel.value,
                "status": conv.status.value,
                "last_message": {
                    "content": last_message.content[:100] if last_message else "",
                    "direction": last_message.direction.value if last_message else None,
                    "created_at": last_message.created_at.isoformat() if last_message else None
                } if last_message else None,
                "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
                "unread_count": unread_count,
                "created_at": conv.created_at.isoformat()
            })
        
        # Calculate channel breakdown
        channel_counts = {}
        for ch in ConversationChannel:
            count_query = db.query(Conversation).join(Lead)
            if user_id:
                count_query = count_query.filter(Lead.user_id == user_id)
            if property_id:
                count_query = count_query.filter(Lead.property_id == property_id)
            channel_counts[ch.value] = count_query.filter(
                Conversation.channel == ch
            ).count()
        
        # Calculate total unread
        unread_query = db.query(Message).join(Conversation).join(Lead)
        if user_id:
            unread_query = unread_query.filter(Lead.user_id == user_id)
        if property_id:
            unread_query = unread_query.filter(Lead.property_id == property_id)
        total_unread = unread_query.filter(
            Message.direction == MessageDirection.inbound
        ).count()
        
        return {
            "conversations": inbox_items,
            "total": total,
            "unread_count": total_unread,
            "channel_breakdown": channel_counts,
            "pagination": {
                "skip": skip,
                "limit": limit,
                "has_more": total > skip + limit
            }
        }
        
    except Exception as e:
        raise DatabaseError(f"Failed to retrieve inbox: {str(e)}")


async def get_conversation_history(
    db: Session,
    conversation_id: UUID,
    skip: int = 0,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Get full conversation history with messages.
    
    Args:
        db: Database session
        conversation_id: Conversation UUID
        skip: Number of messages to skip
        limit: Maximum number of messages to return
        
    Returns:
        Dictionary with conversation details and messages
        
    Raises:
        NotFoundError: If conversation not found
    """
    # Get conversation
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()
    
    if not conversation:
        raise NotFoundError(
            f"Conversation with ID {conversation_id} not found",
            "Conversation"
        )
    
    # Get messages
    messages_query = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.asc())
    
    total_messages = messages_query.count()
    messages = messages_query.offset(skip).limit(limit).all()
    
    # Format messages
    formatted_messages = [
        {
            "id": str(msg.id),
            "direction": msg.direction.value,
            "content": msg.content,
            "sender": msg.sender,
            "recipient": msg.recipient,
            "metadata": msg.extra_data,
            "created_at": msg.created_at.isoformat()
        }
        for msg in messages
    ]
    
    return {
        "conversation": {
            "id": str(conversation.id),
            "lead_id": str(conversation.lead_id),
            "lead_name": conversation.lead.name if conversation.lead else "Unknown",
            "channel": conversation.channel.value,
            "status": conversation.status.value,
            "created_at": conversation.created_at.isoformat(),
            "last_message_at": conversation.last_message_at.isoformat() if conversation.last_message_at else None
        },
        "messages": formatted_messages,
        "total_messages": total_messages,
        "pagination": {
            "skip": skip,
            "limit": limit,
            "has_more": total_messages > skip + limit
        }
    }


async def mark_as_read(
    db: Session,
    conversation_id: UUID,
    message_ids: Optional[List[UUID]] = None
) -> Dict[str, Any]:
    """
    Mark messages in a conversation as read.
    
    Args:
        db: Database session
        conversation_id: Conversation UUID
        message_ids: Optional list of specific message IDs to mark as read.
                    If None, marks all messages in conversation as read.
        
    Returns:
        Dictionary with success status and count of messages marked
        
    Raises:
        NotFoundError: If conversation not found
        DatabaseError: If database operation fails
    """
    try:
        # Verify conversation exists
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise NotFoundError(
                f"Conversation with ID {conversation_id} not found",
                "Conversation"
            )
        
        # Query messages to mark
        query = db.query(Message).filter(
            and_(
                Message.conversation_id == conversation_id,
                Message.direction == MessageDirection.inbound
            )
        )
        
        if message_ids:
            query = query.filter(Message.id.in_(message_ids))
        
        # Update metadata to mark as read
        messages = query.all()
        marked_count = 0
        
        for msg in messages:
            if msg.extra_data is None:
                msg.extra_data = {}
            if not msg.extra_data.get("read", False):
                msg.extra_data["read"] = True
                msg.extra_data["read_at"] = str(UUID())  # placeholder for timestamp
                marked_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "conversation_id": str(conversation_id),
            "messages_marked": marked_count
        }
        
    except NotFoundError:
        raise
    except Exception as e:
        db.rollback()
        raise DatabaseError(f"Failed to mark messages as read: {str(e)}")


def get_conversations(
    db: Session,
    user_id: UUID,
    filters: Dict[str, Any],
    skip: int = 0,
    limit: int = 50
) -> List[Conversation]:
    """Get filtered list of conversations."""
    query = db.query(Conversation).join(Lead).filter(Lead.user_id == user_id)
    
    if 'channel' in filters:
        query = query.filter(Conversation.channel == filters['channel'])
    
    if 'status' in filters:
        query = query.filter(Conversation.status == filters['status'])
    
    if 'search' in filters and filters['search']:
        search_term = f"%{filters['search']}%"
        query = query.filter(
            or_(
                Lead.name.ilike(search_term),
                Lead.email.ilike(search_term),
                Lead.phone.ilike(search_term)
            )
        )
    
    return query.order_by(desc(Conversation.last_message_at)).offset(skip).limit(limit).all()


def get_conversation(
    db: Session,
    conversation_id: UUID,
    include_messages: bool = False
) -> Optional[Conversation]:
    """Get conversation by ID with optional messages."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    if conv and include_messages:
        conv.messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc()).all()
    
    return conv


def send_message(
    db: Session,
    conversation_id: UUID,
    content: str,
    user_id: UUID
) -> Optional[Message]:
    """Send message in a conversation."""
    from datetime import datetime
    
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        return None
    
    message = Message(
        conversation_id=conversation_id,
        direction=MessageDirection.outbound,
        content=content,
        sender="agent",
        recipient=conv.lead.phone or conv.lead.email or "unknown"
    )
    
    db.add(message)
    conv.last_message_at = datetime.utcnow()
    db.commit()
    db.refresh(message)
    
    return message


def update_conversation_status(
    db: Session,
    conversation_id: UUID,
    new_status: ConversationStatus
) -> Optional[Conversation]:
    """Update conversation status."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    if not conv:
        return None
    
    conv.status = new_status
    db.commit()
    db.refresh(conv)
    
    return conv


def mark_conversation_read(
    db: Session,
    conversation_id: UUID,
    user_id: UUID
) -> bool:
    """Mark all messages in conversation as read."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    if not conv:
        return False
    
    messages = db.query(Message).filter(
        and_(
            Message.conversation_id == conversation_id,
            Message.direction == MessageDirection.inbound
        )
    ).all()
    
    for msg in messages:
        if msg.extra_data is None:
            msg.extra_data = {}
        msg.extra_data["read"] = True
    
    db.commit()
    return True


def get_unread_count(db: Session, user_id: UUID) -> int:
    """Get count of unread messages."""
    return db.query(Message).join(Conversation).join(Lead).filter(
        and_(
            Lead.user_id == user_id,
            Message.direction == MessageDirection.inbound
        )
    ).count()


def process_incoming_sms(db: Session, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process incoming SMS from Twilio webhook."""
    from datetime import datetime
    
    phone_from = webhook_data.get("From", "")
    phone_to = webhook_data.get("To", "")
    body = webhook_data.get("Body", "")
    
    # Find or create lead by phone
    lead = db.query(Lead).filter(Lead.phone == phone_from).first()
    
    if not lead:
        from app.models.lead import LeadSource, LeadStatus
        lead = Lead(
            name=f"SMS Lead {phone_from}",
            phone=phone_from,
            source=LeadSource.direct,
            status=LeadStatus.new,
            user_id=UUID("00000000-0000-0000-0000-000000000000")  # Placeholder
        )
        db.add(lead)
        db.flush()
    
    # Find or create conversation
    conv = db.query(Conversation).filter(
        and_(
            Conversation.lead_id == lead.id,
            Conversation.channel == ConversationChannel.sms
        )
    ).first()
    
    if not conv:
        conv = Conversation(
            lead_id=lead.id,
            channel=ConversationChannel.sms,
            status=ConversationStatus.open
        )
        db.add(conv)
        db.flush()
    
    # Create message
    message = Message(
        conversation_id=conv.id,
        direction=MessageDirection.inbound,
        content=body,
        sender=phone_from,
        recipient=phone_to,
        metadata=webhook_data
    )
    
    db.add(message)
    conv.last_message_at = datetime.utcnow()
    db.commit()
    
    return {"conversation_id": conv.id, "message_id": message.id}


def get_lead_messages(db: Session, lead_id: UUID) -> List[Dict[str, Any]]:
    """Get all messages for a lead across all conversations."""
    conversations = db.query(Conversation).filter(Conversation.lead_id == lead_id).all()
    
    all_messages = []
    for conv in conversations:
        messages = db.query(Message).filter(
            Message.conversation_id == conv.id
        ).order_by(Message.created_at.asc()).all()
        
        for msg in messages:
            all_messages.append({
                "id": str(msg.id),
                "conversation_id": str(conv.id),
                "channel": conv.channel.value,
                "direction": msg.direction.value,
                "content": msg.content,
                "sender": msg.sender,
                "recipient": msg.recipient,
                "created_at": msg.created_at.isoformat()
            })
    
    return sorted(all_messages, key=lambda x: x["created_at"])

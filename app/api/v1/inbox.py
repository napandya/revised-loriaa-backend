"""Unified inbox API endpoints for multi-channel communications."""

from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.conversation import ConversationChannel, ConversationStatus
from app.schemas.conversation import (
    ConversationResponse,
    ConversationWithMessages,
)
from app.services.inbox_service import (
    get_conversations,
    get_conversation,
    send_message,
    update_conversation_status,
    mark_conversation_read,
    get_unread_count,
)

router = APIRouter(prefix="/inbox", tags=["inbox"])


@router.get("", response_model=List[ConversationResponse])
async def get_unified_inbox(
    channel: Optional[ConversationChannel] = None,
    status: Optional[ConversationStatus] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get unified inbox with optional filters."""
    filters = {}
    if channel:
        filters['channel'] = channel
    if status:
        filters['status'] = status
    if search:
        filters['search'] = search
    
    conversations = get_conversations(
        db=db,
        user_id=current_user.id,
        filters=filters,
        skip=skip,
        limit=limit
    )
    return conversations


@router.get("/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation_details(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get conversation with all messages."""
    conversation = get_conversation(
        db=db,
        conversation_id=conversation_id,
        include_messages=True
    )
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    return conversation


@router.post("/{conversation_id}/messages", status_code=status.HTTP_201_CREATED)
async def send_conversation_message(
    conversation_id: UUID,
    content: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send message in a conversation."""
    message = send_message(
        db=db,
        conversation_id=conversation_id,
        content=content,
        user_id=current_user.id
    )
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    return message


@router.patch("/{conversation_id}/status", response_model=ConversationResponse)
async def update_status(
    conversation_id: UUID,
    new_status: ConversationStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update conversation status (open/closed)."""
    conversation = update_conversation_status(
        db=db,
        conversation_id=conversation_id,
        new_status=new_status
    )
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    return conversation


@router.post("/{conversation_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_as_read(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark conversation as read."""
    success = mark_conversation_read(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    return None


@router.get("/unread/count")
async def get_unread_message_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get unread message count."""
    count = get_unread_count(db=db, user_id=current_user.id)
    return {"unread_count": count}

"""
Unit tests for Inbox Service.
"""

import pytest
from uuid import uuid4
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.conversation import Conversation, ConversationChannel, ConversationStatus
from app.models.message import Message, MessageDirection
from app.models.lead import Lead
from app.models.user import User
from app.services.inbox_service import (
    get_conversations,
    get_conversation,
    send_message,
    update_conversation_status,
    mark_conversation_read,
    get_unread_count,
)


class TestGetConversations:
    """Tests for get_conversations function."""
    
    def test_get_conversations_returns_list(self, db: Session, test_user: User, test_conversation: Conversation):
        """Test that get_conversations returns a list."""
        conversations = get_conversations(db, user_id=test_user.id, filters={})
        assert isinstance(conversations, list)
        assert len(conversations) >= 1
    
    def test_get_conversations_filters_by_channel(self, db: Session, test_user: User, test_conversation: Conversation):
        """Test filtering conversations by channel."""
        conversations = get_conversations(
            db, 
            user_id=test_user.id, 
            filters={"channel": ConversationChannel.sms}
        )
        assert all(conv.channel == ConversationChannel.sms for conv in conversations)
    
    def test_get_conversations_filters_by_status(self, db: Session, test_user: User, test_conversation: Conversation):
        """Test filtering conversations by status."""
        conversations = get_conversations(
            db,
            user_id=test_user.id,
            filters={"status": ConversationStatus.open}
        )
        assert all(conv.status == ConversationStatus.open for conv in conversations)
    
    def test_get_conversations_empty_result(self, db: Session):
        """Test get_conversations with no matching results."""
        conversations = get_conversations(db, user_id=uuid4(), filters={})
        assert conversations == []


class TestGetConversation:
    """Tests for get_conversation function."""
    
    def test_get_conversation_success(self, db: Session, test_conversation: Conversation):
        """Test successful conversation retrieval."""
        conv = get_conversation(db, conversation_id=test_conversation.id)
        assert conv is not None
        assert conv.id == test_conversation.id
    
    def test_get_conversation_with_messages(self, db: Session, test_conversation: Conversation, test_message: Message):
        """Test conversation retrieval with messages."""
        conv = get_conversation(db, conversation_id=test_conversation.id, include_messages=True)
        assert conv is not None
        assert hasattr(conv, 'messages')
        assert len(conv.messages) >= 1
    
    def test_get_conversation_not_found(self, db: Session):
        """Test conversation not found."""
        conv = get_conversation(db, conversation_id=uuid4())
        assert conv is None


class TestSendMessage:
    """Tests for send_message function."""
    
    def test_send_message_success(self, db: Session, test_conversation: Conversation, test_user: User):
        """Test successful message sending."""
        message = send_message(
            db=db,
            conversation_id=test_conversation.id,
            content="Test message content",
            user_id=test_user.id
        )
        
        assert message is not None
        assert message.content == "Test message content"
        assert message.direction == MessageDirection.outbound
    
    def test_send_message_updates_last_message_at(self, db: Session, test_conversation: Conversation, test_user: User):
        """Test that sending message updates last_message_at."""
        original_time = test_conversation.last_message_at
        
        send_message(
            db=db,
            conversation_id=test_conversation.id,
            content="New message",
            user_id=test_user.id
        )
        
        db.refresh(test_conversation)
        assert test_conversation.last_message_at >= original_time
    
    def test_send_message_conversation_not_found(self, db: Session, test_user: User):
        """Test sending message to non-existent conversation."""
        message = send_message(
            db=db,
            conversation_id=uuid4(),
            content="Test",
            user_id=test_user.id
        )
        assert message is None


class TestUpdateConversationStatus:
    """Tests for update_conversation_status function."""
    
    def test_update_status_success(self, db: Session, test_conversation: Conversation):
        """Test successful status update."""
        updated_conv = update_conversation_status(
            db=db,
            conversation_id=test_conversation.id,
            new_status=ConversationStatus.closed
        )
        
        assert updated_conv is not None
        assert updated_conv.status == ConversationStatus.closed
    
    def test_update_status_not_found(self, db: Session):
        """Test updating non-existent conversation."""
        result = update_conversation_status(
            db=db,
            conversation_id=uuid4(),
            new_status=ConversationStatus.closed
        )
        assert result is None


class TestMarkConversationRead:
    """Tests for mark_conversation_read function."""
    
    def test_mark_read_success(self, db: Session, test_conversation: Conversation, test_message: Message, test_user: User):
        """Test marking conversation as read."""
        result = mark_conversation_read(
            db=db,
            conversation_id=test_conversation.id,
            user_id=test_user.id
        )
        assert result is True
    
    def test_mark_read_not_found(self, db: Session, test_user: User):
        """Test marking non-existent conversation as read."""
        result = mark_conversation_read(
            db=db,
            conversation_id=uuid4(),
            user_id=test_user.id
        )
        assert result is False


class TestGetUnreadCount:
    """Tests for get_unread_count function."""
    
    def test_get_unread_count(self, db: Session, test_user: User, test_message: Message):
        """Test getting unread message count."""
        count = get_unread_count(db=db, user_id=test_user.id)
        assert isinstance(count, int)
        assert count >= 0
    
    def test_get_unread_count_no_messages(self, db: Session):
        """Test unread count with no messages."""
        count = get_unread_count(db=db, user_id=uuid4())
        assert count == 0

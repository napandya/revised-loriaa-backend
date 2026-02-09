"""
Service layer for Loriaa AI CRM.

This module exports all business logic services that handle
data access, validation, and business rules.

Services follow these patterns:
- BaseService for standard CRUD operations
- Transaction management with proper error handling
- Logging and auditing
- Integration with external APIs

Python 3.13 Compatible.
"""

from app.services.base_service import BaseService, ReadOnlyService
from app.services.lead_service import (
    get_leads,
    get_lead,
    create_lead,
    update_lead,
    delete_lead,
    add_lead_activity,
    get_lead_activities,
    update_lead_status,
    calculate_lead_score_internal,
    get_pipeline_stats,
)
from app.services.inbox_service import (
    get_unified_inbox,
    get_conversation_history,
    mark_as_read,
    get_conversations,
    get_conversation,
    send_message,
    update_conversation_status,
    mark_conversation_read,
    get_unread_count,
    process_incoming_sms,
    get_lead_messages,
)
from app.services.document_service import (
    get_documents,
    get_document,
    create_document,
    update_document,
    delete_document,
    search_documents,
)
from app.services.scoring_service import (
    score_leads,
    calculate_lead_score,
)

__all__ = [
    # Base
    "BaseService",
    "ReadOnlyService",
    
    # Leads
    "get_leads",
    "get_lead",
    "create_lead",
    "update_lead",
    "delete_lead",
    "add_lead_activity",
    "get_lead_activities",
    "update_lead_status",
    "calculate_lead_score_internal",
    "get_pipeline_stats",
    
    # Inbox
    "get_unified_inbox",
    "get_conversation_history",
    "mark_as_read",
    "get_conversations",
    "get_conversation",
    "send_message",
    "update_conversation_status",
    "mark_conversation_read",
    "get_unread_count",
    "process_incoming_sms",
    "get_lead_messages",
    
    # Documents
    "get_documents",
    "get_document",
    "create_document",
    "update_document",
    "delete_document",
    "search_documents",
    
    # Scoring
    "score_leads",
    "calculate_lead_score",
]

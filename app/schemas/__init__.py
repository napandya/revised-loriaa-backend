"""Pydantic schemas for request/response validation."""

from app.schemas.user import UserCreate, UserResponse, Token, TokenData
from app.schemas.bot import BotCreate, BotUpdate, BotResponse
from app.schemas.call_log import CallLogCreate, CallLogResponse
from app.schemas.team import TeamMemberCreate, TeamMemberUpdate, TeamMemberResponse
from app.schemas.knowledge_base import DocumentCreate, DocumentResponse, QueryRequest
from app.schemas.billing import BillingStats, MonthlyBilling

# Phase 3 schemas
from app.schemas.lead import (
    LeadBase,
    LeadCreate,
    LeadUpdate,
    LeadResponse,
    LeadWithActivities,
    LeadPipelineStats,
    LeadActivityResponse,
)
from app.schemas.conversation import (
    ConversationBase,
    ConversationCreate,
    ConversationResponse,
    ConversationWithMessages,
    MessageResponse,
)
from app.schemas.document import (
    DocumentBase,
    DocumentUpdate,
    DocumentQuery,
    DocumentSearchResult,
)
from app.schemas.dashboard import (
    DashboardMetrics,
    MarketingFunnelData,
    LeasingVelocityData,
    LeasingVelocityDataPoint,
    AgentActivityFeed,
    AgentActivityItem,
    PortfolioHealthScore,
    PropertyHealthMetrics,
)
from app.schemas.agent import (
    AgentRequest,
    AgentResponse,
    AgentTaskStatus,
    AgentActivityLog,
)
from app.schemas.voice import (
    VapiWebhookEvent,
    VapiCallRequest,
    VapiCallResponse,
    VapiCallDetails,
    VapiAssistantConfig,
    VapiFunctionCall,
    VapiTranscript,
)
from app.schemas.integration import (
    IntegrationConfigBase,
    IntegrationConfigCreate,
    IntegrationConfigUpdate,
    IntegrationConfigResponse,
    FacebookLeadWebhook,
    FacebookLeadData,
    TwilioMessageWebhook,
    IntegrationStatus,
)

__all__ = [
    # User schemas
    "UserCreate",
    "UserResponse",
    "Token",
    "TokenData",
    # Bot schemas
    "BotCreate",
    "BotUpdate",
    "BotResponse",
    # Call log schemas
    "CallLogCreate",
    "CallLogResponse",
    # Team schemas
    "TeamMemberCreate",
    "TeamMemberUpdate",
    "TeamMemberResponse",
    # Knowledge base schemas
    "DocumentCreate",
    "DocumentResponse",
    "QueryRequest",
    # Billing schemas
    "BillingStats",
    "MonthlyBilling",
    # Lead schemas
    "LeadBase",
    "LeadCreate",
    "LeadUpdate",
    "LeadResponse",
    "LeadWithActivities",
    "LeadPipelineStats",
    "LeadActivityResponse",
    # Conversation schemas
    "ConversationBase",
    "ConversationCreate",
    "ConversationResponse",
    "ConversationWithMessages",
    "MessageResponse",
    # Document schemas (Phase 3)
    "DocumentBase",
    "DocumentUpdate",
    "DocumentQuery",
    "DocumentSearchResult",
    # Dashboard schemas
    "DashboardMetrics",
    "MarketingFunnelData",
    "LeasingVelocityData",
    "LeasingVelocityDataPoint",
    "AgentActivityFeed",
    "AgentActivityItem",
    "PortfolioHealthScore",
    "PropertyHealthMetrics",
    # Agent schemas
    "AgentRequest",
    "AgentResponse",
    "AgentTaskStatus",
    "AgentActivityLog",
    # Voice/Vapi schemas
    "VapiWebhookEvent",
    "VapiCallRequest",
    "VapiCallResponse",
    "VapiCallDetails",
    "VapiAssistantConfig",
    "VapiFunctionCall",
    "VapiTranscript",
    # Integration schemas
    "IntegrationConfigBase",
    "IntegrationConfigCreate",
    "IntegrationConfigUpdate",
    "IntegrationConfigResponse",
    "FacebookLeadWebhook",
    "FacebookLeadData",
    "TwilioMessageWebhook",
    "IntegrationStatus",
]

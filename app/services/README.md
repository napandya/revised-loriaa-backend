# Business Logic Services

This directory contains the core business logic services for the Loriaa AI Backend Phase 4 implementation.

## Services Overview

### 1. `lead_service.py` - Lead Management
Handles all lead-related business logic including:
- **CRUD operations**: Create, read, update, delete leads
- **Status management**: Update lead status with activity tracking
- **Pipeline analytics**: Calculate pipeline statistics and conversion rates
- **Lead scoring**: Internal scoring based on multiple factors
- **Lead assignment**: Logic for assigning leads to property managers

**Key Functions:**
- `create_lead(db, lead_data)` - Create new lead with initial activity
- `update_lead(db, lead_id, lead_data)` - Update lead with change tracking
- `get_lead(db, lead_id)` - Retrieve single lead
- `list_leads(db, filters...)` - List leads with filtering
- `update_lead_status(db, lead_id, new_status)` - Update status with activity log
- `get_pipeline_stats(db, filters...)` - Calculate pipeline metrics

### 2. `scoring_service.py` - AI Lead Scoring
AI-powered intelligent lead scoring using Google Gemini:
- **Gemini integration**: Uses Gemini 2.0 Flash for intelligent scoring
- **Multi-factor analysis**: Considers source, engagement, response time, budget, timeline
- **Fallback scoring**: Uses rule-based scoring if API unavailable
- **Explanation generation**: Provides reasoning for scores

**Key Functions:**
- `calculate_lead_score(db, lead)` - Main scoring function using AI
- `_fallback_scoring(db, lead)` - Backup rule-based scoring

**Scoring Factors:**
- Lead source quality (0-25 points)
- Status progression (0-25 points)
- Engagement level/activities (0-25 points)
- Response time (0-15 points)
- Budget & timeline from metadata (0-10 points)

### 3. `inbox_service.py` - Unified Inbox
Multi-channel inbox aggregation service:
- **Channel aggregation**: Combines SMS, email, voice, chat into unified view
- **Conversation management**: Track conversations with leads
- **Message history**: Retrieve full conversation threads
- **Read/unread tracking**: Mark messages as read

**Key Functions:**
- `get_unified_inbox(db, filters...)` - Get all conversations across channels
- `get_conversation_history(db, conversation_id)` - Get full message thread
- `mark_as_read(db, conversation_id, message_ids)` - Mark messages as read

### 4. `analytics_service.py` - Analytics & Metrics
COO Command Center analytics and insights:
- **Dashboard metrics**: Calculate KPIs for overview dashboard
- **Marketing funnel**: Track conversion through funnel stages
- **Leasing velocity**: Time-series data for leasing trends
- **Agent activity**: Track AI agent actions and performance
- **Portfolio health**: Multi-property health scoring

**Key Functions:**
- `get_dashboard_metrics(db, filters...)` - Overall dashboard KPIs
- `get_marketing_funnel(db, property_id, days)` - Funnel conversion data
- `get_leasing_velocity(db, property_id, days)` - Time-series leasing data
- `get_agent_activity_feed(db, limit)` - Recent AI agent actions
- `get_portfolio_health(db, user_id)` - Portfolio-wide health metrics

**Metrics Calculated:**
- Total leads, active conversations, tours scheduled
- Applications pending, leases signed
- Occupancy rate, revenue
- AI call minutes, average response time
- Conversion rates by stage

### 5. `document_service.py` - Document Management
Document processing with AI embeddings and semantic search:
- **Embedding generation**: Uses OpenAI ada-002 for 1536-dim embeddings
- **Vector storage**: Stores embeddings in pgvector
- **Semantic search**: Cosine similarity search for relevant documents
- **Category management**: Organize by policy, procedure, FAQ, training

**Key Functions:**
- `create_document(db, title, content, category, property_id, user_id)` - Create with embedding
- `generate_embedding(text)` - Generate OpenAI embedding vector
- `search_documents(db, query, filters...)` - Semantic search
- `get_document(db, document_id)` - Retrieve single document
- `delete_document(db, doc_id)` - Delete document
- `list_documents(db, filters...)` - List with filters

**Search Features:**
- Semantic similarity using pgvector cosine distance
- Filter by property, category, user
- Top-K retrieval with similarity scores

### 6. `notification_service.py` - Notifications
Multi-channel notification delivery:
- **Email notifications**: SendGrid integration for transactional emails
- **SMS notifications**: Twilio integration for SMS alerts
- **In-app notifications**: Database-stored notifications (model needed)
- **Template formatting**: HTML email templates

**Key Functions:**
- `send_email(to, subject, body, html_body)` - Send via SendGrid
- `send_sms(to, body)` - Send via Twilio
- `create_notification(db, user_id, title, message, type)` - In-app notification
- `send_notification_email(to, type, title, message)` - Formatted email
- `send_lead_notification(db, user_id, lead_name, ...)` - Multi-channel lead alerts

**Notification Types:**
- `info` - General information
- `success` - Success messages
- `warning` - Warning alerts
- `error` - Error notifications

## Configuration

All services use settings from `app/core/config.py`:

```python
# Required for scoring_service.py
GOOGLE_API_KEY = "your-google-api-key"
GEMINI_MODEL = "gemini-2.0-flash-exp"

# Required for document_service.py
OPENAI_API_KEY = "your-openai-api-key"

# Required for notification_service.py
SENDGRID_API_KEY = "your-sendgrid-api-key"
FROM_EMAIL = "noreply@loriaa.ai"
TWILIO_ACCOUNT_SID = "your-twilio-sid"
TWILIO_AUTH_TOKEN = "your-twilio-token"
TWILIO_PHONE_NUMBER = "+1234567890"
```

## Error Handling

All services use custom exceptions from `app/core/exceptions.py`:
- `NotFoundError` - Resource not found (404)
- `ValidationError` - Input validation errors (422)
- `IntegrationError` - External API failures (503)
- `DatabaseError` - Database operation errors (500)
- `AuthenticationError` - Auth failures (401)
- `AuthorizationError` - Permission errors (403)

## Database Session Management

Services use dependency injection for database sessions:

```python
from sqlalchemy.orm import Session
from app.api.deps import get_db

@router.get("/leads")
async def list_leads_endpoint(
    db: Session = Depends(get_db),
    property_id: Optional[UUID] = None
):
    leads = await list_leads(db, property_id=property_id)
    return leads
```

## Usage Examples

### Lead Management
```python
from app.services.lead_service import create_lead, update_lead_status
from app.schemas.lead import LeadCreate

# Create lead
lead_data = LeadCreate(
    property_id=property_uuid,
    user_id=user_uuid,
    name="John Doe",
    email="john@example.com",
    phone="+1234567890",
    source=LeadSource.website,
    status=LeadStatus.new
)
lead = await create_lead(db, lead_data)

# Update status
lead = await update_lead_status(
    db, 
    lead.id, 
    LeadStatus.contacted,
    notes="Initial contact made via phone"
)
```

### AI Scoring
```python
from app.services.scoring_service import calculate_lead_score

# Score a lead using Gemini AI
result = await calculate_lead_score(db, lead)
print(f"Score: {result['score']}/100")
print(f"Explanation: {result['explanation']}")

# Update lead with new score
lead.score = result['score']
lead.metadata = lead.metadata or {}
lead.metadata['scoring'] = result
db.commit()
```

### Document Search
```python
from app.services.document_service import search_documents

# Semantic search
results = await search_documents(
    db,
    query="pet policy for small dogs",
    property_id=property_uuid,
    top_k=5
)

for doc in results:
    print(f"{doc['title']}: {doc['similarity_score']}")
```

### Notifications
```python
from app.services.notification_service import send_lead_notification

# Multi-channel notification
result = await send_lead_notification(
    db,
    user_id=manager_uuid,
    lead_name="Jane Smith",
    notification_type="info",
    message="New lead from website contact form",
    send_email_notification=True,
    send_sms_notification=True,
    user_email="manager@property.com",
    user_phone="+1234567890"
)
```

## Testing

Run tests with pytest:
```bash
pytest app/tests/services/
```

## Future Enhancements

1. **Notification Model**: Create proper Notification database model
2. **Caching**: Add Redis caching for frequently accessed data
3. **Background Jobs**: Move heavy operations to Celery tasks
4. **Rate Limiting**: Add rate limiting for external API calls
5. **Batch Operations**: Add bulk operations for efficiency
6. **Advanced Analytics**: Machine learning for predictive analytics
7. **Real-time Updates**: WebSocket support for real-time notifications

## Dependencies

All required packages in `requirements.txt`:
- `google-generativeai>=0.8.0` - Gemini AI
- `openai>=1.12.0` - OpenAI embeddings
- `sendgrid>=6.11.0` - Email delivery
- `twilio>=8.10.0` - SMS delivery
- `pgvector==0.2.4` - Vector similarity search
- `sqlalchemy==2.0.25` - ORM
- `fastapi==0.109.0` - Web framework

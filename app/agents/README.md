# AI Agent System - Phase 6

This directory contains the complete AI agent system for the Loriaa platform, built using OpenAI GPT-4o with function calling.

## Architecture

### Agent Hierarchy

```
COOAgent (Orchestrator)
├── LeasingAgent (Workforce)
├── MarketingAgent (Workforce)
└── PropertyAgent (Workforce)
```

### Components

#### 1. Base Agent (`base.py`)
- Abstract base class for all agents
- OpenAI GPT-4o integration with function calling
- Function/tool calling support
- Activity logging to database
- Error handling and retries

#### 2. COO Orchestrator (`orchestrator.py`)
- Routes requests to appropriate workforce agents
- Intent classification (leasing, marketing, property_management)
- Multi-agent task coordination
- Request analysis and breakdown

#### 3. Workforce Agents

##### Leasing Agent (`workforce/leasing_agent.py`)
Specializes in:
- Lead qualification
- Tour scheduling and management
- Lead follow-ups
- Application processing
- Communication with prospects

**Tools:**
- `lead_tools`: Get/update/score leads
- `communication_tools`: SMS/email
- `scheduling_tools`: Tour scheduling

##### Marketing Agent (`workforce/marketing_agent.py`)
Specializes in:
- Campaign performance analysis
- Lead source optimization
- ROI analysis
- Budget recommendations
- Conversion funnel analysis

**Tools:**
- `analytics_tools`: Metrics and analytics
- `integration_tools`: Ad platform integration

##### Property Agent (`workforce/property_agent.py`)
Specializes in:
- Policy and procedure questions
- Document Q&A (RAG)
- Compliance guidance
- Training support
- Lease term explanations

**Tools:**
- `document_tools`: RAG/search knowledge base

#### 4. Tools (`tools/`)
Reusable functions that agents can call:

- **lead_tools.py**: Lead management operations
- **communication_tools.py**: SMS/email sending
- **scheduling_tools.py**: Tour scheduling logic
- **document_tools.py**: RAG and document search
- **analytics_tools.py**: Metrics and reporting
- **integration_tools.py**: External API integrations

#### 5. Prompts (`prompts/`)
System prompts defining agent behavior:

- **leasing_prompt.py**: Leasing agent system prompt
- **marketing_prompt.py**: Marketing agent system prompt
- **property_prompt.py**: Property agent system prompt

## Usage

### Basic Usage - COO Routing

```python
from app.agents import COOAgent
from app.database import get_db

db = next(get_db())
coo = COOAgent()

# Automatically routes to the appropriate agent
result = coo.route_request(
    request="Schedule a tour for lead abc-123 tomorrow at 2 PM",
    db=db,
    context={"lead_id": "abc-123"}
)
```

### Direct Agent Usage

```python
from app.agents import LeasingAgent

leasing_agent = LeasingAgent()

# Qualify a lead
result = leasing_agent.qualify_lead(
    lead_id="abc-123",
    db=db
)

# Schedule a tour
result = leasing_agent.schedule_lead_tour(
    lead_id="abc-123",
    date="2024-02-15",
    time_slot="2:00 PM",
    property_id="prop-456",
    db=db
)
```

### Marketing Analysis

```python
from app.agents import MarketingAgent

marketing_agent = MarketingAgent()

# Analyze campaigns
result = marketing_agent.analyze_campaign_performance(
    period="30d",
    db=db
)

# Optimize lead sources
result = marketing_agent.optimize_lead_sources(
    property_id="prop-456",
    period="30d",
    db=db
)
```

### Document Q&A

```python
from app.agents import PropertyAgent

property_agent = PropertyAgent()

# Ask a policy question
result = property_agent.answer_policy_question(
    question="What are the requirements for rental applications?",
    property_id="prop-456",
    db=db
)
```

## Configuration

### Environment Variables

Required environment variables (set in `.env` or `app/core/config.py`):

```bash
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o  # or your preferred model
```

### Database

The agent system uses the following database tables:
- `agent_activities`: Logs all agent actions
- `leads`: Lead information
- `lead_activities`: Lead interaction history
- `documents`: Knowledge base documents

## Tool Development

To add a new tool:

1. Create function in appropriate `tools/*.py` file:

```python
def my_new_tool(param: str, db: Session) -> Dict[str, Any]:
    """
    Tool description for the agent.
    
    Args:
        param: Parameter description
        db: Database session
    
    Returns:
        Dict with result
    """
    try:
        # Implementation
        return {"success": True, "data": "result"}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

2. Add to agent's tool list in `workforce/*.py`:

```python
tools = [
    # ... existing tools
    my_module.my_new_tool
]
```

## Activity Logging

All agent activities are automatically logged to the `agent_activities` table:

```python
{
    "id": "uuid",
    "agent_type": "leasing|marketing|property_manager",
    "action": "execute_task",
    "result": "completed|error",
    "metadata": {"task": "...", "context": {...}},
    "lead_id": "uuid|null",
    "created_at": "timestamp"
}
```

## Error Handling

The agent system includes comprehensive error handling:

- Automatic retries for API failures
- Graceful degradation when tools fail
- Error logging to database and application logs
- User-friendly error messages

## Testing

Run the examples:

```bash
python -m app.agents.examples
```

Run tests (when available):

```bash
pytest tests/agents/
```

## Future Enhancements

- [ ] Agent memory/conversation history
- [ ] Custom tool creation via API
- [ ] Agent performance metrics dashboard
- [ ] A/B testing for different prompts
- [ ] Multi-turn conversations
- [ ] Agent collaboration workflows
- [ ] Real-time streaming responses

## API Integration

The agents can be exposed via API endpoints:

```python
@router.post("/agents/execute")
async def execute_agent_task(
    request: AgentRequest,
    db: Session = Depends(get_db)
):
    coo = COOAgent()
    result = coo.route_request(
        request=request.task,
        db=db,
        context=request.context
    )
    return result
```

## Monitoring

Monitor agent performance through:
- Database queries on `agent_activities`
- Application logs
- Response times and success rates
- Tool usage statistics

## Support

For questions or issues with the agent system, see:
- Main documentation: `SERVICES_IMPLEMENTATION.md`
- Example usage: `app/agents/examples.py`
- Tool documentation: Individual `tools/*.py` files

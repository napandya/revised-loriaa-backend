# Vapi Voice Integration

Complete voice call integration for Loriaa AI using Vapi.ai API.

## Overview

This integration enables voice-based lead engagement through AI-powered phone assistants. It includes:

- **Vapi Client**: HTTP client for Vapi API operations
- **Webhook Handlers**: Event processing for call lifecycle and function calling
- **Assistant Management**: Configuration and deployment of voice assistants
- **REST API**: FastAPI endpoints for managing assistants and calls

## Components

### 1. Client (`integrations/vapi/client.py`)

HTTP client with async/await support for Vapi API:

- `create_assistant()` - Create new voice assistant
- `update_assistant()` - Update assistant configuration
- `delete_assistant()` - Remove assistant
- `make_outbound_call()` - Initiate outbound calls
- `get_call()` - Get call details
- `list_calls()` - List calls with filtering

### 2. Webhooks (`integrations/vapi/webhooks.py`)

Event handlers for Vapi webhooks:

- `handle_webhook()` - Main webhook router
- `on_call_started()` - Track call initiation
- `on_call_ended()` - Save call logs and transcripts
- `on_function_call()` - Route function calls to handlers
- Signature verification with HMAC

**Function Handlers:**
- `check_availability()` - Unit availability lookup
- `schedule_tour()` - Tour scheduling with lead creation
- `qualify_lead()` - Lead scoring and qualification
- `transfer_to_human()` - Human agent transfer

### 3. Assistants (`integrations/vapi/assistants.py`)

Assistant configuration and management:

- `create_property_assistant()` - Create assistant for property
- `configure_assistant_functions()` - Add function calling
- `update_assistant_knowledge()` - Update knowledge base
- Default system prompts for leasing agents
- ElevenLabs voice support

### 4. API Endpoints (`api/v1/voice.py`)

REST API for voice operations:

**Assistants:**
- `POST /api/v1/voice/assistants` - Create assistant
- `GET /api/v1/voice/assistants/{id}` - Get assistant
- `PUT /api/v1/voice/assistants/{id}` - Update assistant
- `DELETE /api/v1/voice/assistants/{id}` - Delete assistant

**Calls:**
- `POST /api/v1/voice/call` - Make outbound call
- `GET /api/v1/voice/calls` - List calls
- `GET /api/v1/voice/calls/{id}` - Get call details

**Webhooks:**
- `POST /api/v1/voice/webhook` - Receive Vapi events (no auth)

## Configuration

Required environment variables:

```bash
# Vapi Configuration
VAPI_API_KEY=your_vapi_api_key
VAPI_WEBHOOK_SECRET=your_webhook_secret
VAPI_BASE_URL=https://api.vapi.ai

# Optional: ElevenLabs for premium voices
ELEVENLABS_API_KEY=your_elevenlabs_key
```

## Usage Examples

### Create Assistant

```python
POST /api/v1/voice/assistants?property_id={bot_id}
{
  "name": "Sunset Apartments",
  "first_message": "Hello! Thank you for calling Sunset Apartments.",
  "system_prompt": "You are a helpful leasing agent...",
  "voice_id": "en-US-Neural2-F",
  "model": "gpt-4"
}
```

### Make Outbound Call

```python
POST /api/v1/voice/call
{
  "phone_number": "+15551234567",
  "assistant_id": "asst_123",
  "lead_id": "uuid",
  "metadata": {"campaign": "follow_up"}
}
```

### Webhook Events

Vapi sends webhooks for:

- `call.started` - Call begins
- `call.ended` - Call completes (saves to DB)
- `function-call` - Assistant invokes function
- `transcript` - Real-time transcript updates
- `status-update` - Call status changes

## Database Integration

### Call Logs
All calls are logged in `call_logs` table with:
- Duration, status, transcript
- Recording URL
- Bot/property association

### Lead Activities
Call events create `lead_activities`:
- Tour scheduling
- Lead qualification
- Status changes
- Transfer requests

### Lead Management
Automatic lead creation/update:
- Source: "phone"
- Status progression
- Score calculation
- Metadata tracking

## Security

- Webhook signature verification via HMAC-SHA256
- JWT authentication for API endpoints
- User ownership verification for all operations
- No authentication on webhook endpoint (verified by signature)

## Error Handling

All errors raised as `VoiceError` with:
- HTTP 503 status
- Detailed error messages
- Context in details dict

## Testing

Test assistant with:
```python
# In assistants.py
await test_assistant(assistant_id, test_phone_number)
```

## Future Enhancements

- [ ] Real-time call monitoring dashboard
- [ ] Call analytics and sentiment analysis
- [ ] Integration with PMS for real availability
- [ ] Voicemail detection and handling
- [ ] Multi-language support
- [ ] Call recording transcription with Whisper
- [ ] Advanced call routing and IVR

## Dependencies

- `httpx>=0.26.0` - Async HTTP client
- `fastapi` - API framework
- `sqlalchemy` - Database ORM
- `pydantic` - Schema validation

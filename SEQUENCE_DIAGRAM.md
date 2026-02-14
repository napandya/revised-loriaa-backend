# Backend — Sequence Diagrams

All diagrams use [Mermaid](https://mermaid.js.org/) syntax and render natively on GitHub.

---

## 1. User Authentication Flow

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend (React)
    participant API as FastAPI Backend
    participant MW as Middleware Stack
    participant Auth as Auth Router
    participant Security as Security Module
    participant DB as PostgreSQL

    User->>FE: Enter email & password
    FE->>API: POST /api/v1/auth/login (form data)
    API->>MW: GZip → Security Headers → Request Logger → CORS
    MW->>Auth: Route to auth handler
    Auth->>DB: SELECT user WHERE email = ?
    DB-->>Auth: User record
    Auth->>Security: verify_password(plain, hashed)
    Security-->>Auth: Match ✓
    Auth->>Security: create_access_token(user_id, email)
    Security-->>Auth: JWT token
    Auth-->>API: {access_token, token_type}
    API-->>FE: 200 OK + JWT
    FE->>FE: Store token in localStorage
    FE-->>User: Redirect to /dashboard
```

---

## 2. AI Agent Chat Flow (Leasing / Marketing / Property)

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend
    participant API as FastAPI
    participant Router as Agent Router
    participant Orchestrator as COO Orchestrator
    participant Agent as Specialist Agent<br/>(Leasing/Marketing/Property)
    participant Gemini as Google Gemini API
    participant Tools as Agent Tools
    participant DB as PostgreSQL

    User->>FE: Type message in agent chat
    FE->>API: POST /api/v1/agents/{type}/execute<br/>Authorization: Bearer JWT
    API->>Router: Validate token → route
    Router->>Orchestrator: analyze_and_route(message)
    Orchestrator->>Gemini: Classify intent
    Gemini-->>Orchestrator: Intent + target agent
    Orchestrator->>Agent: execute(message, context)
    Agent->>Gemini: Send prompt + tools schema
    Gemini-->>Agent: Function call request (e.g. search_leads)
    Agent->>Tools: Call tool function
    Tools->>DB: Query data
    DB-->>Tools: Results
    Tools-->>Agent: Tool output
    Agent->>Gemini: Send tool results
    Gemini-->>Agent: Final natural language response
    Agent->>DB: Log to agent_activities
    Agent-->>Router: AgentResponse
    Router-->>API: JSON response
    API-->>FE: 200 OK + agent reply
    FE-->>User: Display response in chat
```

---

## 3. Ad Copy Generation Flow (ChatGPT)

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend
    participant API as FastAPI
    participant AdRouter as Ad Copy Router
    participant Service as ContentGenerationService
    participant OpenAI as OpenAI GPT-4o API
    participant DB as PostgreSQL

    User->>FE: Select platform, objective, enter property details
    FE->>API: POST /api/v1/ad-copy/generate<br/>{platform, objective, property_details, num_variations}
    API->>AdRouter: Validate request schema
    AdRouter->>Service: generate_ad_copy(request)
    Service->>Service: Build platform-specific prompt<br/>(char limits, Fair Housing rules)
    Service->>OpenAI: ChatCompletion(model="gpt-4o",<br/>messages=[system_prompt, user_prompt],<br/>response_format=json)
    OpenAI-->>Service: JSON with ad variations
    Service->>Service: Parse & validate response
    Service-->>AdRouter: AdCopyResponse(variations, platform_specs)
    AdRouter-->>API: JSON response
    API-->>FE: 200 OK + ad copy variations
    FE-->>User: Display variations with copy-to-clipboard
```

---

## 4. Voice Assistant Flow (VAPI)

```mermaid
sequenceDiagram
    actor Caller
    participant Phone as Phone Network
    participant VAPI as VAPI Platform
    participant API as FastAPI Backend
    participant VoiceRouter as Voice Router
    participant VAPIClient as VAPI Integration Client
    participant DB as PostgreSQL

    Note over Caller,DB: Assistant Creation
    API->>VAPIClient: create_assistant(name, prompt, voice)
    VAPIClient->>VAPI: POST /assistants
    VAPI-->>VAPIClient: assistant_id
    VAPIClient-->>API: Assistant created

    Note over Caller,DB: Inbound Call
    Caller->>Phone: Dial property number
    Phone->>VAPI: Route to VAPI assistant
    VAPI->>VAPI: AI voice conversation
    VAPI->>API: POST /api/v1/voice/webhooks/vapi<br/>(call events: started, ended, transcript)
    API->>VoiceRouter: Process webhook payload
    VoiceRouter->>DB: Create/update call_logs
    VoiceRouter->>DB: Create/update leads (if new prospect)
    VoiceRouter-->>VAPI: 200 OK
    VAPI-->>Caller: Continue conversation

    Note over Caller,DB: Outbound Call
    API->>VAPIClient: make_call(phone, assistant_id)
    VAPIClient->>VAPI: POST /calls
    VAPI->>Phone: Initiate call
    Phone->>Caller: Ring
```

---

## 5. Lead Management & Scoring Flow

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend
    participant API as FastAPI
    participant LeadRouter as Lead Router
    participant LeadService as Lead Service
    participant Scoring as Scoring Service
    participant Gemini as Google Gemini API
    participant DB as PostgreSQL

    User->>FE: Create new lead
    FE->>API: POST /api/v1/leads<br/>{name, email, phone, source}
    API->>LeadRouter: Validate + authorize
    LeadRouter->>LeadService: create_lead(data)
    LeadService->>DB: INSERT INTO leads
    DB-->>LeadService: lead record
    LeadService->>DB: INSERT INTO lead_activities (status: new)
    LeadService-->>LeadRouter: Lead created
    LeadRouter-->>FE: 201 Created + lead

    Note over User,DB: AI Lead Scoring
    User->>FE: Click "Score Lead"
    FE->>API: POST /api/v1/agents/leasing/qualify-lead
    API->>Scoring: calculate_lead_score(lead)
    Scoring->>DB: Fetch lead + activities
    DB-->>Scoring: Lead data + history
    Scoring->>Gemini: Score this lead (source, status, engagement, budget)
    Gemini-->>Scoring: {score: 85, explanation: "..."}
    alt Gemini unavailable
        Scoring->>Scoring: _fallback_scoring() (rule-based)
    end
    Scoring->>DB: UPDATE lead SET score = 85
    Scoring-->>API: {score, explanation}
    API-->>FE: 200 OK
    FE-->>User: Show score + explanation
```

---

## 6. Knowledge Base / RAG Flow

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend
    participant API as FastAPI
    participant KBRouter as Knowledge Base Router
    participant DocService as Document Service
    participant Embeddings as OpenAI Embeddings
    participant DB as PostgreSQL + pgvector

    Note over User,DB: Document Upload
    User->>FE: Upload document
    FE->>API: POST /api/v1/kb/documents<br/>{bot_id, title, content}
    API->>KBRouter: Validate request
    KBRouter->>DocService: process_document(data)
    DocService->>DocService: Chunk text into segments
    DocService->>Embeddings: Generate embeddings (text-embedding-ada-002)
    Embeddings-->>DocService: Vector embeddings [1536 dims]
    DocService->>DB: INSERT INTO knowledge_base<br/>(content, embedding, metadata)
    DocService-->>KBRouter: Document stored
    KBRouter-->>FE: 201 Created

    Note over User,DB: RAG Chat Query
    User->>FE: Ask question in property agent chat
    FE->>API: POST /api/v1/kb/chat<br/>{bot_id, query}
    API->>KBRouter: Route to chat handler
    KBRouter->>Embeddings: Embed query text
    Embeddings-->>KBRouter: Query vector
    KBRouter->>DB: SELECT * FROM knowledge_base<br/>ORDER BY embedding <=> query_vector<br/>LIMIT 5
    DB-->>KBRouter: Top-5 similar chunks
    KBRouter->>KBRouter: Build prompt with retrieved context
    KBRouter-->>FE: 200 OK + AI answer with sources
    FE-->>User: Display answer
```

---

## 7. Integration Flow (Facebook / Google Ads / Twilio)

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend
    participant API as FastAPI
    participant IntRouter as Integration Router
    participant IntService as Integration Service
    participant ExtAPI as External API<br/>(Facebook / Google Ads / Twilio)
    participant DB as PostgreSQL

    Note over User,DB: Configure Integration
    User->>FE: Enter API keys in Settings
    FE->>API: PUT /api/v1/settings/integrations<br/>{provider, credentials}
    API->>IntService: save_config(provider, encrypted_creds)
    IntService->>DB: UPSERT integration_configs
    IntService-->>FE: Config saved ✓

    Note over User,DB: Use Integration (e.g., Facebook Ad)
    User->>FE: Request via Marketing Agent
    FE->>API: POST /api/v1/agents/marketing/execute
    API->>IntRouter: Agent calls integration tool
    IntRouter->>DB: Fetch integration config
    DB-->>IntRouter: Decrypted credentials
    IntRouter->>ExtAPI: API call (e.g., create ad campaign)
    ExtAPI-->>IntRouter: Response
    IntRouter-->>API: Tool result
    API-->>FE: Agent response with integration data
    FE-->>User: Display results
```

---

## 8. Application Startup Sequence

```mermaid
sequenceDiagram
    participant Docker as Docker Compose
    participant DB as PostgreSQL
    participant Redis as Redis
    participant App as FastAPI App
    participant MW as Middleware
    participant Routes as Route Registry

    Docker->>DB: Start pgvector/pgvector:pg15
    Docker->>Redis: Start redis:7-alpine
    DB->>DB: Run init-db.sql
    DB-->>Docker: Healthy (pg_isready ✓)
    Redis-->>Docker: Healthy (redis-cli ping ✓)

    Docker->>App: Start backend container
    App->>App: create_application()
    App->>App: Register exception handlers
    App->>MW: Add GZip, Security, Logging, CORS
    App->>Routes: Register all routers (auth, bots, agents, etc.)
    App->>App: lifespan() startup
    App->>DB: create_tables() via SQLAlchemy
    App->>DB: check_database_health()
    DB-->>App: {status: healthy, pool_size: 20}
    App->>App: uvicorn.run(host=0.0.0.0, port=8000)
    App-->>Docker: Backend ready ✓

    Docker->>Docker: Start frontend container
    Note over Docker: yarn dev --host 0.0.0.0 --port 3000
```

# Backend Enterprise Setup Instructions

This document provides instructions for setting up the enterprise-grade Loriaa AI Backend.

## Python 3.13 Compatibility

This codebase is fully compatible with Python 3.13:
- Uses `from __future__ import annotations` for forward references
- Uses `datetime.now(timezone.utc)` instead of deprecated `datetime.utcnow()`
- Type hints use `dict[str, Any]` syntax instead of `Dict[str, Any]`
- No deprecated standard library features

---

## New Enterprise Features

### 1. Custom Exception Hierarchy (`app/core/exceptions.py`)
- **ErrorCode enum** - Standardized error codes for API responses
- **LoriaaException** - Base exception with logging, correlation IDs, timestamps
- **Specialized exceptions**:
  - `AuthenticationError`, `TokenExpiredError`, `TokenInvalidError`
  - `ValidationError`, `MissingFieldError`, `DuplicateEntryError`
  - `NotFoundError`, `ResourceConflictError`, `ResourceLockedError`
  - `DatabaseError`, `DatabaseConnectionError`, `DatabaseTransactionError`
  - `IntegrationError`, `IntegrationTimeoutError`, `IntegrationRateLimitError`
  - `AgentError`, `AgentExecutionError`, `AgentQuotaExceededError`
  - `VoiceError`, `VoiceCallError`, `VoiceWebhookError`
  - `RateLimitError`, `BusinessRuleViolationError`

### 2. Enhanced Database Layer (`app/database.py`)
- **Connection pooling** with QueuePool
- **Pool health monitoring** with pre-ping
- **Transaction management** context managers
- **Bulk operations** for efficient inserts/updates
- **Health check endpoint** with pool statistics

### 3. Security Enhancements (`app/core/security.py`)
- **Password strength validation**
- **Refresh token support**
- **Security headers middleware**
- **Token type validation** (access vs refresh)

### 4. Structured Logging (`app/core/logging.py`)
- **JSON format** for production (ELK/Splunk compatible)
- **Pretty format** for development (colored output)
- **Correlation ID tracking**
- **Library noise reduction**

### 5. API Dependencies (`app/api/deps.py`)
- **Type-annotated dependencies** using `Annotated`
- **Pagination utilities** with metadata
- **Common filters** (search, sort)
- **Resource ownership validation**
- **Role-based access control** factory

### 6. Base Service Pattern (`app/services/base_service.py`)
- **Generic CRUD operations**
- **Automatic error handling**
- **Bulk operations support**
- **Transaction management**
- **Logging integration**

---

## Files Modified/Created

### Core Module (`app/core/`)
| File | Description |
|------|-------------|
| `__init__.py` | Exports all core utilities |
| `config.py` | Settings with Pydantic v2 |
| `exceptions.py` | **NEW** - Enterprise exception hierarchy |
| `security.py` | **ENHANCED** - Refresh tokens, password validation |
| `logging.py` | **NEW** - Structured logging configuration |

### Database (`app/database.py`)
- **REWRITTEN** - Connection pooling, health checks, transactions

### Main Application (`app/main.py`)
- **REWRITTEN** - Application factory, middleware, lifespan events

### API Layer (`app/api/deps.py`)
- **REWRITTEN** - Type-annotated dependencies, pagination, RBAC

### Services (`app/services/`)
| File | Description |
|------|-------------|
| `__init__.py` | Exports all services |
| `base_service.py` | **NEW** - Generic CRUD base class |
| `lead_service.py` | Fixed search filter bug |

### Tests (`tests/`)
| File | Description |
|------|-------------|
| `conftest.py` | Test configuration and fixtures |
| `test_lead_service.py` | Unit tests for lead service |
| `test_inbox_service.py` | Unit tests for inbox service |
| `test_document_service.py` | Unit tests for document service |
| `test_api_integration.py` | Integration tests for all endpoints |

---

## Setup Instructions

### Step 1: Extract Files

```bash
# Extract the zip to your backend directory
unzip backend_enterprise_update.zip -d /path/to/loriaa-ai-backend/
```

### Step 2: Install Dependencies

```bash
# Using pip
pip install -r requirements.txt

# Or with Docker
docker-compose build
```

### Step 3: Run Migrations

```bash
# Apply database migrations
alembic upgrade head
```

### Step 4: Seed Database

```bash
# Run comprehensive seed script
python scripts/seed_comprehensive.py
```

### Step 5: Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run only unit tests
pytest tests/test_*_service.py -v

# Run only integration tests
pytest tests/test_api_integration.py -v
```

### Step 6: Start the Server

```bash
# Development
uvicorn app.main:app --reload --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## API Response Format

### Success Response
```json
{
  "id": "uuid",
  "name": "Resource Name",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "RES_3001",
    "message": "Lead with ID 'abc-123' not found",
    "details": {
      "resource_type": "Lead",
      "resource_id": "abc-123"
    },
    "correlation_id": "req_1705318200123",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

---

## Error Codes Reference

| Code | Name | HTTP Status |
|------|------|-------------|
| AUTH_1001 | Invalid Credentials | 401 |
| AUTH_1002 | Token Expired | 401 |
| AUTH_1003 | Token Invalid | 401 |
| AUTH_1004 | Insufficient Permissions | 403 |
| VAL_2001 | Validation Failed | 422 |
| VAL_2004 | Duplicate Entry | 409 |
| RES_3001 | Resource Not Found | 404 |
| DB_4001 | Database Error | 500 |
| INT_5001 | Integration Error | 503 |
| AGT_6001 | Agent Error | 500 |
| RATE_8001 | Rate Limit Exceeded | 429 |

---

## Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/loriaa

# Security
SECRET_KEY=your-secure-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment
ENVIRONMENT=development  # or production

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]

# AI/ML (optional)
GOOGLE_API_KEY=your-google-api-key
OPENAI_API_KEY=your-openai-api-key

# Integrations (optional)
VAPI_API_KEY=your-vapi-key
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
```

---

## Docker Compose Example

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://loriaa:password@db:5432/loriaa
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=production
    depends_on:
      - db

  db:
    image: pgvector/pgvector:pg15
    environment:
      - POSTGRES_USER=loriaa
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=loriaa
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

---

## Test Credentials

```
Email: demo@loriaa.ai
Password: password123
```

# Loriaa AI CRM - Docker Development Setup

This guide explains how to run the full Loriaa AI CRM stack using Docker Compose.

## Prerequisites

- Docker Desktop (or Docker Engine + Docker Compose)
- Git

## Quick Start

```bash
# 1. Clone or organize your repos
mkdir loriaa-crm && cd loriaa-crm

# Copy/clone backend and frontend repos
# - ./backend/ should contain the FastAPI backend
# - ./frontend/ should contain the React frontend

# 2. Copy environment file
cp .env.example .env

# 3. Start all services
make up
# Or without make:
docker compose up -d

# 4. Seed the database
make seed
# Or:
docker compose exec backend python scripts/seed_comprehensive.py
```

## Services

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | React + Vite application |
| Backend | http://localhost:8000 | FastAPI REST API |
| API Docs | http://localhost:8000/docs | Swagger documentation |
| PostgreSQL | localhost:5432 | Database with pgvector |
| Redis | localhost:6379 | Caching & task queue |

## Directory Structure

```
loriaa-crm/
├── backend/                 # FastAPI backend
│   ├── app/
│   ├── scripts/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/               # React frontend
│   ├── src/
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .env.example
├── .env                    # Your local config (not committed)
└── Makefile
```

## Common Commands

### Using Makefile (recommended)

```bash
# Setup
make setup          # Initial setup
make build          # Rebuild images

# Run
make up             # Start services
make down           # Stop services
make restart        # Restart services

# Development
make logs           # View all logs
make logs-b         # Backend logs only
make logs-f         # Frontend logs only
make shell-b        # Backend bash shell
make shell-db       # PostgreSQL psql shell

# Database
make seed           # Seed demo data
make migrate        # Run migrations
make reset-db       # Reset database (DESTRUCTIVE)

# Testing
make test           # Run all tests
make test-cov       # Tests with coverage
```

### Using Docker Compose directly

```bash
# Start
docker compose up -d

# Stop
docker compose down

# View logs
docker compose logs -f backend

# Run command in container
docker compose exec backend python scripts/seed_comprehensive.py

# Access shell
docker compose exec backend bash
docker compose exec frontend sh
docker compose exec db psql -U loriaa -d loriaa
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# Required
POSTGRES_PASSWORD=your-secure-password
SECRET_KEY=your-32-character-minimum-secret-key

# Optional - AI/ML
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...

# Optional - Integrations
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
```

## Development Workflow

### Backend Development

The backend directory is mounted as a volume, so changes are reflected immediately with hot reload:

```bash
# Make changes to backend/app/...
# Server automatically reloads
```

### Frontend Development

The frontend also has hot reload enabled:

```bash
# Make changes to frontend/src/...
# Browser automatically refreshes
```

### Running Tests

```bash
# All tests
make test

# With coverage report
make test-cov

# Specific test file
docker compose exec backend pytest tests/test_lead_service.py -v
```

### Database Migrations

```bash
# Apply migrations
make migrate

# Create new migration
make makemigrations
# Enter: "add new field to leads table"

# Reset database
make reset-db
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker compose logs backend

# Rebuild
docker compose build --no-cache backend
docker compose up -d
```

### Database connection issues

```bash
# Check if db is healthy
docker compose ps

# Access database directly
docker compose exec db psql -U loriaa -d loriaa
```

### Frontend can't connect to backend

1. Check backend is running: `docker compose ps`
2. Check CORS settings in backend
3. Verify `VITE_BACKEND_URL` in frontend/.env

### Clear everything and start fresh

```bash
make clean
make setup
make up
make seed
```

## Production Deployment

For production, use the production Docker Compose override:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

Key production changes:
- Disable debug mode
- Use proper SECRET_KEY
- Enable HTTPS
- Configure proper CORS origins
- Use gunicorn instead of uvicorn

## Test Credentials

```
Email: demo@loriaa.ai
Password: password123
```

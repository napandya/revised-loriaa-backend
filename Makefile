# =============================================================
# Loriaa AI CRM - Makefile
# Common commands for development
# =============================================================

.PHONY: help build up down restart logs shell test seed clean

# Default target
help:
	@echo "Loriaa AI CRM - Development Commands"
	@echo "====================================="
	@echo ""
	@echo "Setup:"
	@echo "  make setup     - Initial setup (copy .env, build images)"
	@echo "  make build     - Build all Docker images"
	@echo ""
	@echo "Run:"
	@echo "  make up        - Start all services"
	@echo "  make down      - Stop all services"
	@echo "  make restart   - Restart all services"
	@echo "  make up-celery - Start with Celery workers"
	@echo ""
	@echo "Development:"
	@echo "  make logs      - View all logs"
	@echo "  make logs-b    - View backend logs"
	@echo "  make logs-f    - View frontend logs"
	@echo "  make shell-b   - Backend shell"
	@echo "  make shell-db  - Database shell (psql)"
	@echo ""
	@echo "Database:"
	@echo "  make seed      - Seed database with demo data"
	@echo "  make migrate   - Run database migrations"
	@echo "  make reset-db  - Reset database (DESTRUCTIVE)"
	@echo ""
	@echo "Testing:"
	@echo "  make test      - Run all tests"
	@echo "  make test-cov  - Run tests with coverage"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean     - Remove containers and volumes"

# ============================================================
# Setup
# ============================================================

setup:
	@echo "Setting up Loriaa AI CRM..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env file"; fi
	@docker compose build
	@echo "Setup complete! Run 'make up' to start."

build:
	docker compose build --no-cache

# ============================================================
# Run Services
# ============================================================

up:
	docker compose up -d
	@echo ""
	@echo "Services started!"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Backend:  http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"

down:
	docker compose down

restart:
	docker compose restart

up-celery:
	docker compose --profile with-celery up -d
	@echo "Started with Celery workers"

# ============================================================
# Logs & Shell
# ============================================================

logs:
	docker compose logs -f

logs-b:
	docker compose logs -f backend

logs-f:
	docker compose logs -f frontend

logs-db:
	docker compose logs -f db

shell-b:
	docker compose exec backend bash

shell-f:
	docker compose exec frontend sh

shell-db:
	docker compose exec db psql -U loriaa -d loriaa

# ============================================================
# Database
# ============================================================

seed:
	docker compose exec backend python scripts/seed_comprehensive.py

migrate:
	docker compose exec backend alembic upgrade head

makemigrations:
	@read -p "Migration message: " msg; \
	docker compose exec backend alembic revision --autogenerate -m "$$msg"

reset-db:
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " confirm; \
	if [ "$$confirm" = "y" ]; then \
		docker compose down -v; \
		docker compose up -d db; \
		sleep 5; \
		docker compose up -d; \
		sleep 10; \
		make migrate; \
		make seed; \
		echo "Database reset complete!"; \
	fi

# ============================================================
# Testing
# ============================================================

test:
	docker compose exec backend pytest -v

test-cov:
	docker compose exec backend pytest --cov=app --cov-report=html --cov-report=term-missing

test-unit:
	docker compose exec backend pytest tests/test_*_service.py -v

test-api:
	docker compose exec backend pytest tests/test_api_integration.py -v

# ============================================================
# Cleanup
# ============================================================

clean:
	docker compose down -v --remove-orphans
	docker system prune -f
	@echo "Cleanup complete!"

clean-all:
	docker compose down -v --remove-orphans
	docker system prune -af
	@echo "Full cleanup complete!"

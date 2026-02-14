"""
Enterprise-grade FastAPI application for Loriaa AI CRM.

This module provides:
- Application factory with proper configuration
- CORS and security middleware
- Global exception handling
- Health check endpoints
- Graceful startup/shutdown

Python 3.13 Compatible.
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.exceptions import (
    LoriaaException,
    loriaa_exception_handler,
    generic_exception_handler,
    register_exception_handlers
)
from app.core.security import get_security_headers
from app.database import create_tables, check_database_health

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.ENVIRONMENT == "production" else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================================
# Middleware
# ============================================================

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Generate correlation ID
        correlation_id = request.headers.get(
            "X-Correlation-ID",
            f"req_{int(time.time() * 1000)}"
        )
        
        # Log request
        logger.info(
            f"Request started",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else "unknown"
            }
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log response
        logger.info(
            f"Request completed",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2)
            }
        )
        
        # Add correlation ID to response
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        for header, value in get_security_headers().items():
            response.headers[header] = value
        
        return response


# ============================================================
# Application Lifespan
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown.
    
    Startup:
    - Create database tables
    - Verify database connection
    - Initialize caches
    
    Shutdown:
    - Close database connections
    - Cleanup resources
    """
    # Startup
    logger.info("=" * 60)
    logger.info("Starting Loriaa AI Backend")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info("=" * 60)
    
    try:
        # Create database tables
        logger.info("Creating database tables...")
        create_tables()
        
        # Verify database connection
        logger.info("Verifying database connection...")
        health = check_database_health()
        if health["status"] != "healthy":
            logger.error(f"Database health check failed: {health}")
            raise RuntimeError("Database health check failed")
        
        logger.info(f"Database connection healthy: {health}")
        logger.info(f"CORS Origins: {settings.cors_origins_list}")
        logger.info("Application startup complete")
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Loriaa AI Backend...")
    logger.info("Cleanup complete")


# ============================================================
# Application Factory
# ============================================================

def create_application() -> FastAPI:
    """
    Application factory for creating the FastAPI app.
    
    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="Loriaa AI Backend",
        description="Enterprise-grade AI-powered Property Management CRM Backend",
        version="2.0.0",
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
        openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
        lifespan=lifespan
    )
    
    # Register exception handlers
    register_exception_handlers(app)
    
    # Add middleware (order matters - last added is first executed)
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Correlation-ID", "X-Response-Time"]
    )
    
    # Register routes
    _register_routes(app)
    
    return app


def _register_routes(app: FastAPI) -> None:
    """Register all API routes."""
    
    # Import routers
    from app.api.v1 import (
        auth, bots, call_logs, teams, billing, knowledge_base, dashboard, voice,
        leads, inbox, documents, settings as settings_router, ad_copy
    )
    from app.api.v1.agents import leasing, marketing, property as property_agent
    from app.api.v1.integrations import facebook, google_ads, twilio, resman
    
    # Health endpoints
    @app.get("/", tags=["Health"])
    async def root():
        """Root endpoint."""
        return {
            "service": "Loriaa AI Backend",
            "version": "2.0.0",
            "status": "running"
        }
    
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "Loriaa AI Backend",
            "environment": settings.ENVIRONMENT
        }
    
    @app.get("/health/detailed", tags=["Health"])
    async def detailed_health_check():
        """Detailed health check with database status."""
        db_health = check_database_health()
        
        return {
            "status": "healthy" if db_health["status"] == "healthy" else "degraded",
            "service": "Loriaa AI Backend",
            "version": "2.0.0",
            "environment": settings.ENVIRONMENT,
            "components": {
                "database": db_health,
                "api": {"status": "healthy"}
            }
        }
    
    @app.get("/api/health", tags=["Health"])
    async def api_health():
        """API-prefixed health check for load balancers."""
        return {"status": "healthy"}
    
    # Core API routers
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(bots.router, prefix="/api/v1/bots", tags=["Bots"])
    app.include_router(call_logs.router, prefix="/api/v1/call-logs", tags=["Call Logs"])
    app.include_router(teams.router, prefix="/api/v1/teams", tags=["Teams"])
    app.include_router(billing.router, prefix="/api/v1/billing", tags=["Billing"])
    app.include_router(knowledge_base.router, prefix="/api/v1/kb", tags=["Knowledge Base"])
    app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
    app.include_router(voice.router, prefix="/api/v1/voice", tags=["Voice"])
    
    # CRM-specific routers
    app.include_router(leads.router, prefix="/api/v1", tags=["Leads"])
    app.include_router(inbox.router, prefix="/api/v1", tags=["Inbox"])
    app.include_router(documents.router, prefix="/api/v1", tags=["Documents"])
    app.include_router(settings_router.router, prefix="/api/v1", tags=["Settings"])
    
    # AI Agent routers
    app.include_router(leasing.router, prefix="/api/v1", tags=["Agents", "Leasing"])
    app.include_router(marketing.router, prefix="/api/v1", tags=["Agents", "Marketing"])
    app.include_router(property_agent.router, prefix="/api/v1", tags=["Agents", "Property"])
    
    # Integration routers
    app.include_router(facebook.router, prefix="/api/v1", tags=["Integrations", "Facebook"])
    app.include_router(google_ads.router, prefix="/api/v1", tags=["Integrations", "Google Ads"])
    app.include_router(twilio.router, prefix="/api/v1", tags=["Integrations", "Twilio"])
    app.include_router(resman.router, prefix="/api/v1", tags=["Integrations", "ResMan"])
    
    # Content generation (ChatGPT ad copy)
    app.include_router(ad_copy.router, prefix="/api/v1/ad-copy", tags=["Ad Copy", "Content Generation"])


# ============================================================
# Application Instance
# ============================================================

# Create the application instance
app = create_application()

"""
Enterprise-grade database connection and session management.

This module provides:
- Connection pooling with health checks
- Session management with proper error handling
- Database health monitoring
- Transaction management utilities

Python 3.13 Compatible.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError, OperationalError, IntegrityError
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool

from app.core.config import settings
from app.core.exceptions import (
    DatabaseConnectionError,
    DatabaseQueryError,
    DatabaseTransactionError,
    DatabaseError
)

logger = logging.getLogger(__name__)


# ============================================================
# Database Engine Configuration
# ============================================================

def create_db_engine(database_url: Optional[str] = None) -> Engine:
    """
    Create SQLAlchemy engine with enterprise-grade configuration.
    
    Features:
    - Connection pooling with QueuePool
    - Pool pre-ping for connection health
    - Optimized pool size and overflow
    - Statement timeout configuration
    
    Args:
        database_url: Optional database URL override
        
    Returns:
        Configured SQLAlchemy Engine
    """
    url = database_url or settings.DATABASE_URL
    
    # Connection pool configuration
    pool_config = {
        "poolclass": QueuePool,
        "pool_size": 10,  # Base pool size
        "max_overflow": 20,  # Additional connections when pool is full
        "pool_timeout": 30,  # Wait time for available connection
        "pool_recycle": 1800,  # Recycle connections after 30 minutes
        "pool_pre_ping": True,  # Verify connections before use
    }
    
    # Create engine with configuration
    engine = create_engine(
        url,
        echo=settings.ENVIRONMENT == "development",  # SQL logging in dev
        **pool_config
    )
    
    # Register event listeners for connection management
    _register_engine_events(engine)
    
    logger.info(
        f"Database engine created",
        extra={
            "pool_size": pool_config["pool_size"],
            "max_overflow": pool_config["max_overflow"],
            "environment": settings.ENVIRONMENT
        }
    )
    
    return engine


def _register_engine_events(engine: Engine) -> None:
    """Register event listeners for the database engine."""
    
    @event.listens_for(engine, "connect")
    def on_connect(dbapi_connection, connection_record):
        """Configure connection on checkout."""
        logger.debug("New database connection established")
    
    @event.listens_for(engine, "checkout")
    def on_checkout(dbapi_connection, connection_record, connection_proxy):
        """Log connection checkout from pool."""
        logger.debug("Connection checked out from pool")
    
    @event.listens_for(engine, "checkin")
    def on_checkin(dbapi_connection, connection_record):
        """Log connection return to pool."""
        logger.debug("Connection returned to pool")
    
    @event.listens_for(engine, "invalidate")
    def on_invalidate(dbapi_connection, connection_record, exception):
        """Log connection invalidation."""
        logger.warning(f"Connection invalidated: {exception}")


# ============================================================
# Global Engine and Session Factory
# ============================================================

# Create the global engine
engine = create_db_engine()

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Prevent lazy loading issues
)

# Base class for all models
Base = declarative_base()


# ============================================================
# Session Management
# ============================================================

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions.
    
    Provides a database session that is automatically closed
    after the request completes.
    
    Yields:
        SQLAlchemy Session
        
    Raises:
        DatabaseConnectionError: If database connection fails
    """
    session = SessionLocal()
    try:
        yield session
    except OperationalError as e:
        logger.error(f"Database operational error: {e}")
        raise DatabaseConnectionError(cause=e)
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        session.rollback()
        raise DatabaseQueryError("session", cause=e)
    finally:
        session.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions outside of FastAPI requests.
    
    Usage:
        with get_db_session() as db:
            db.query(User).all()
    
    Yields:
        SQLAlchemy Session
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except OperationalError as e:
        logger.error(f"Database operational error: {e}")
        session.rollback()
        raise DatabaseConnectionError(cause=e)
    except IntegrityError as e:
        logger.error(f"Database integrity error: {e}")
        session.rollback()
        raise DatabaseError(
            message="Database integrity constraint violated",
            operation="transaction",
            cause=e
        )
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        session.rollback()
        raise DatabaseTransactionError("context_session", cause=e)
    finally:
        session.close()


@contextmanager
def transaction(session: Session) -> Generator[Session, None, None]:
    """
    Context manager for explicit transaction handling.
    
    Provides a nested transaction that can be committed or rolled back
    independently.
    
    Usage:
        with transaction(db) as tx:
            tx.add(new_object)
            # Commits on exit, rolls back on exception
    
    Args:
        session: SQLAlchemy session
        
    Yields:
        The same session for chaining operations
    """
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Transaction failed: {e}")
        raise DatabaseTransactionError("explicit_transaction", cause=e)


# ============================================================
# Database Health and Utilities
# ============================================================

def check_database_health() -> dict:
    """
    Check database connection health.
    
    Returns:
        Dictionary with health status and details
    """
    try:
        with get_db_session() as db:
            # Simple query to verify connection
            result = db.execute(text("SELECT 1 as health"))
            row = result.fetchone()
            
            if row and row[0] == 1:
                # Get pool statistics
                pool_status = engine.pool.status()
                
                return {
                    "status": "healthy",
                    "database": "postgresql",
                    "pool_status": pool_status,
                    "pool_size": engine.pool.size(),
                    "checked_out": engine.pool.checkedout(),
                    "overflow": engine.pool.overflow()
                }
            
            return {
                "status": "unhealthy",
                "reason": "Health query returned unexpected result"
            }
            
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "reason": str(e)
        }


def create_tables() -> None:
    """
    Create all database tables defined in the models.
    
    This should be called during application startup or for testing.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Failed to create database tables: {e}")
        raise DatabaseError(
            message="Failed to create database tables",
            operation="create_tables",
            cause=e
        )


def drop_tables() -> None:
    """
    Drop all database tables.
    
    WARNING: This is destructive and should only be used in testing.
    """
    if settings.ENVIRONMENT == "production":
        raise RuntimeError("Cannot drop tables in production environment")
    
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("All database tables dropped")
    except SQLAlchemyError as e:
        logger.error(f"Failed to drop database tables: {e}")
        raise DatabaseError(
            message="Failed to drop database tables",
            operation="drop_tables",
            cause=e
        )


def get_table_row_counts() -> dict[str, int]:
    """
    Get row counts for all tables (useful for monitoring).
    
    Returns:
        Dictionary mapping table names to row counts
    """
    counts = {}
    
    with get_db_session() as db:
        for table in Base.metadata.tables.keys():
            try:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                counts[table] = result.scalar() or 0
            except SQLAlchemyError:
                counts[table] = -1  # Indicate error
    
    return counts


# ============================================================
# Bulk Operations
# ============================================================

def bulk_insert(session: Session, objects: list, batch_size: int = 1000) -> int:
    """
    Efficiently insert objects in batches.
    
    Args:
        session: SQLAlchemy session
        objects: List of model instances to insert
        batch_size: Number of objects per batch
        
    Returns:
        Total number of objects inserted
    """
    total_inserted = 0
    
    for i in range(0, len(objects), batch_size):
        batch = objects[i:i + batch_size]
        session.bulk_save_objects(batch)
        session.flush()
        total_inserted += len(batch)
        logger.debug(f"Inserted batch of {len(batch)} objects")
    
    return total_inserted


def bulk_update(
    session: Session,
    model_class,
    mappings: list[dict],
    batch_size: int = 1000
) -> int:
    """
    Efficiently update objects in batches.
    
    Args:
        session: SQLAlchemy session
        model_class: SQLAlchemy model class
        mappings: List of dictionaries with 'id' and fields to update
        batch_size: Number of updates per batch
        
    Returns:
        Total number of objects updated
    """
    total_updated = 0
    
    for i in range(0, len(mappings), batch_size):
        batch = mappings[i:i + batch_size]
        session.bulk_update_mappings(model_class, batch)
        session.flush()
        total_updated += len(batch)
        logger.debug(f"Updated batch of {len(batch)} objects")
    
    return total_updated

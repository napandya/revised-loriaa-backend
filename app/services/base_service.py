"""
Base service class for enterprise-grade service layer.

This module provides:
- Base service with common CRUD operations
- Transaction management
- Error handling patterns
- Logging utilities

Python 3.13 Compatible.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, Optional, TypeVar
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.database import Base
from app.core.exceptions import (
    NotFoundError,
    DatabaseError,
    DatabaseQueryError,
    DatabaseTransactionError,
    DuplicateEntryError
)

logger = logging.getLogger(__name__)

# Type variables for generic service
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType], ABC):
    """
    Abstract base service providing common CRUD operations.
    
    Provides:
    - Standard CRUD methods with error handling
    - Transaction management
    - Logging
    - Pagination support
    
    Subclasses must implement:
    - model_class property
    - resource_name property
    """
    
    @property
    @abstractmethod
    def model_class(self) -> type[ModelType]:
        """Return the SQLAlchemy model class."""
        pass
    
    @property
    @abstractmethod
    def resource_name(self) -> str:
        """Return the human-readable resource name for error messages."""
        pass
    
    def __init__(self, db: Session):
        """
        Initialize service with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    # ========================================================
    # Read Operations
    # ========================================================
    
    def get_by_id(self, id: UUID) -> Optional[ModelType]:
        """
        Get a record by its ID.
        
        Args:
            id: The record UUID
            
        Returns:
            The record or None if not found
        """
        try:
            return self.db.query(self.model_class).filter(
                self.model_class.id == id
            ).first()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting {self.resource_name} by ID: {e}")
            raise DatabaseQueryError(f"get_{self.resource_name}", cause=e)
    
    def get_by_id_or_raise(self, id: UUID) -> ModelType:
        """
        Get a record by ID or raise NotFoundError.
        
        Args:
            id: The record UUID
            
        Returns:
            The record
            
        Raises:
            NotFoundError: If record not found
        """
        record = self.get_by_id(id)
        if record is None:
            raise NotFoundError(
                resource_type=self.resource_name,
                resource_id=str(id)
            )
        return record
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[dict[str, Any]] = None
    ) -> list[ModelType]:
        """
        Get all records with pagination and optional filters.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            filters: Optional filter dictionary
            
        Returns:
            List of records
        """
        try:
            query = self.db.query(self.model_class)
            query = self._apply_filters(query, filters or {})
            return query.offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error listing {self.resource_name}s: {e}")
            raise DatabaseQueryError(f"list_{self.resource_name}s", cause=e)
    
    def count(self, filters: Optional[dict[str, Any]] = None) -> int:
        """
        Count records matching filters.
        
        Args:
            filters: Optional filter dictionary
            
        Returns:
            Count of matching records
        """
        try:
            query = self.db.query(self.model_class)
            query = self._apply_filters(query, filters or {})
            return query.count()
        except SQLAlchemyError as e:
            self.logger.error(f"Error counting {self.resource_name}s: {e}")
            raise DatabaseQueryError(f"count_{self.resource_name}s", cause=e)
    
    def exists(self, id: UUID) -> bool:
        """
        Check if a record exists.
        
        Args:
            id: The record UUID
            
        Returns:
            True if record exists
        """
        return self.get_by_id(id) is not None
    
    # ========================================================
    # Write Operations
    # ========================================================
    
    def create(self, data: CreateSchemaType) -> ModelType:
        """
        Create a new record.
        
        Args:
            data: Creation data (Pydantic schema or dict)
            
        Returns:
            The created record
            
        Raises:
            DuplicateEntryError: If unique constraint violated
            DatabaseTransactionError: If transaction fails
        """
        try:
            # Convert Pydantic model to dict if needed
            if hasattr(data, 'model_dump'):
                data_dict = data.model_dump(exclude_unset=True)
            elif hasattr(data, 'dict'):
                data_dict = data.dict(exclude_unset=True)
            else:
                data_dict = data
            
            record = self.model_class(**data_dict)
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
            
            self.logger.info(f"Created {self.resource_name}: {record.id}")
            return record
            
        except IntegrityError as e:
            self.db.rollback()
            self.logger.warning(f"Integrity error creating {self.resource_name}: {e}")
            raise DuplicateEntryError(
                resource_type=self.resource_name,
                field="unknown",
                value="unknown"
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(f"Error creating {self.resource_name}: {e}")
            raise DatabaseTransactionError(f"create_{self.resource_name}", cause=e)
    
    def update(self, id: UUID, data: UpdateSchemaType) -> ModelType:
        """
        Update an existing record.
        
        Args:
            id: The record UUID
            data: Update data (Pydantic schema or dict)
            
        Returns:
            The updated record
            
        Raises:
            NotFoundError: If record not found
            DatabaseTransactionError: If transaction fails
        """
        record = self.get_by_id_or_raise(id)
        
        try:
            # Convert Pydantic model to dict if needed
            if hasattr(data, 'model_dump'):
                update_dict = data.model_dump(exclude_unset=True)
            elif hasattr(data, 'dict'):
                update_dict = data.dict(exclude_unset=True)
            else:
                update_dict = data
            
            # Apply updates
            for field, value in update_dict.items():
                if hasattr(record, field):
                    setattr(record, field, value)
            
            self.db.commit()
            self.db.refresh(record)
            
            self.logger.info(f"Updated {self.resource_name}: {id}")
            return record
            
        except IntegrityError as e:
            self.db.rollback()
            self.logger.warning(f"Integrity error updating {self.resource_name}: {e}")
            raise DuplicateEntryError(
                resource_type=self.resource_name,
                field="unknown",
                value="unknown"
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(f"Error updating {self.resource_name}: {e}")
            raise DatabaseTransactionError(f"update_{self.resource_name}", cause=e)
    
    def delete(self, id: UUID) -> bool:
        """
        Delete a record.
        
        Args:
            id: The record UUID
            
        Returns:
            True if deleted, False if not found
        """
        record = self.get_by_id(id)
        if record is None:
            return False
        
        try:
            self.db.delete(record)
            self.db.commit()
            
            self.logger.info(f"Deleted {self.resource_name}: {id}")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(f"Error deleting {self.resource_name}: {e}")
            raise DatabaseTransactionError(f"delete_{self.resource_name}", cause=e)
    
    def delete_or_raise(self, id: UUID) -> bool:
        """
        Delete a record or raise NotFoundError.
        
        Args:
            id: The record UUID
            
        Returns:
            True if deleted
            
        Raises:
            NotFoundError: If record not found
        """
        if not self.delete(id):
            raise NotFoundError(
                resource_type=self.resource_name,
                resource_id=str(id)
            )
        return True
    
    # ========================================================
    # Bulk Operations
    # ========================================================
    
    def bulk_create(self, items: list[CreateSchemaType]) -> list[ModelType]:
        """
        Create multiple records in a single transaction.
        
        Args:
            items: List of creation data
            
        Returns:
            List of created records
        """
        try:
            records = []
            for data in items:
                if hasattr(data, 'model_dump'):
                    data_dict = data.model_dump(exclude_unset=True)
                elif hasattr(data, 'dict'):
                    data_dict = data.dict(exclude_unset=True)
                else:
                    data_dict = data
                
                record = self.model_class(**data_dict)
                self.db.add(record)
                records.append(record)
            
            self.db.commit()
            
            for record in records:
                self.db.refresh(record)
            
            self.logger.info(f"Bulk created {len(records)} {self.resource_name}s")
            return records
            
        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(f"Error bulk creating {self.resource_name}s: {e}")
            raise DatabaseTransactionError(f"bulk_create_{self.resource_name}s", cause=e)
    
    def bulk_delete(self, ids: list[UUID]) -> int:
        """
        Delete multiple records.
        
        Args:
            ids: List of record UUIDs
            
        Returns:
            Number of records deleted
        """
        try:
            deleted = self.db.query(self.model_class).filter(
                self.model_class.id.in_(ids)
            ).delete(synchronize_session='fetch')
            
            self.db.commit()
            
            self.logger.info(f"Bulk deleted {deleted} {self.resource_name}s")
            return deleted
            
        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(f"Error bulk deleting {self.resource_name}s: {e}")
            raise DatabaseTransactionError(f"bulk_delete_{self.resource_name}s", cause=e)
    
    # ========================================================
    # Filter Helpers
    # ========================================================
    
    def _apply_filters(self, query, filters: dict[str, Any]):
        """
        Apply filters to a query. Override in subclass for custom filtering.
        
        Args:
            query: SQLAlchemy query object
            filters: Dictionary of filters
            
        Returns:
            Filtered query
        """
        return query


class ReadOnlyService(Generic[ModelType], ABC):
    """
    Read-only service for entities that should not be modified through this layer.
    
    Useful for:
    - Audit logs
    - System configurations
    - Reference data
    """
    
    @property
    @abstractmethod
    def model_class(self) -> type[ModelType]:
        """Return the SQLAlchemy model class."""
        pass
    
    @property
    @abstractmethod
    def resource_name(self) -> str:
        """Return the human-readable resource name."""
        pass
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def get_by_id(self, id: UUID) -> Optional[ModelType]:
        """Get a record by ID."""
        return self.db.query(self.model_class).filter(
            self.model_class.id == id
        ).first()
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> list[ModelType]:
        """Get all records with pagination."""
        return self.db.query(self.model_class).offset(skip).limit(limit).all()
    
    def count(self) -> int:
        """Count all records."""
        return self.db.query(self.model_class).count()

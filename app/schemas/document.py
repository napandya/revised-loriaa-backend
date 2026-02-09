"""Document schemas for knowledge base and document management."""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from app.models.document import DocumentCategory


class DocumentBase(BaseModel):
    """Base document schema."""
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    category: DocumentCategory
    file_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentCreate(DocumentBase):
    """Schema for creating a new document."""
    user_id: UUID
    property_id: Optional[UUID] = None


class DocumentUpdate(BaseModel):
    """Schema for updating a document."""
    title: Optional[str] = Field(None, min_length=1)
    content: Optional[str] = Field(None, min_length=1)
    category: Optional[DocumentCategory] = None
    file_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentResponse(DocumentBase):
    """Schema for document response."""
    id: UUID
    user_id: UUID
    property_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DocumentQuery(BaseModel):
    """Schema for RAG document queries."""
    query: str = Field(..., min_length=1)
    property_id: Optional[UUID] = None
    category: Optional[DocumentCategory] = None
    top_k: int = Field(default=5, ge=1, le=20)


class DocumentSearchResult(BaseModel):
    """Schema for document search results with similarity score."""
    document: DocumentResponse
    similarity_score: float = Field(..., ge=0, le=1)
    relevant_excerpt: Optional[str] = None

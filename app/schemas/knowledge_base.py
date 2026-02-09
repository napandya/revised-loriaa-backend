"""Knowledge base schemas for RAG and vector search."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID


class DocumentCreate(BaseModel):
    """Schema for creating a new document in knowledge base."""
    bot_id: UUID
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    document_metadata: Optional[Dict[str, Any]] = None


class DocumentResponse(BaseModel):
    """Schema for document response."""
    id: UUID
    bot_id: UUID
    title: str
    content: str
    document_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class QueryRequest(BaseModel):
    """Schema for querying knowledge base."""
    bot_id: UUID
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class QueryResult(BaseModel):
    """Schema for query result."""
    document_id: UUID
    title: str
    content: str
    similarity_score: float
    document_metadata: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    """Schema for RAG-based chat."""
    bot_id: UUID
    message: str = Field(..., min_length=1)
    conversation_history: Optional[List[Dict[str, str]]] = None

"""
OpenAI API endpoints for Loriaa AI CRM.

Provides endpoints for:
- Chat completions
- Lead response generation
- Document embeddings
- Conversation summarization

Python 3.13 Compatible.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.integrations.openai import (
    chat_completion,
    generate_lead_response,
    generate_property_description,
    summarize_conversation,
    generate_embedding,
)
from app.core.exceptions import IntegrationError

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# Request/Response Models
# ============================================================

class ChatRequest(BaseModel):
    """Chat completion request."""
    messages: list[dict] = Field(..., description="List of messages with 'role' and 'content'")
    model: str = Field(default="gpt-4o", description="Model to use")
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=4096)
    system_prompt: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat completion response."""
    response: str
    model: str


class LeadResponseRequest(BaseModel):
    """Lead response generation request."""
    lead_message: str = Field(..., description="The lead's message")
    lead_name: Optional[str] = None
    lead_interest: Optional[str] = None
    property_info: Optional[str] = None
    conversation_history: Optional[list[dict]] = None


class LeadResponseResponse(BaseModel):
    """Lead response generation response."""
    response: str
    ai_generated: bool = True


class PropertyDescriptionRequest(BaseModel):
    """Property description request."""
    beds: int
    baths: float
    sqft: int
    price: str
    amenities: Optional[list[str]] = None
    location: Optional[str] = None
    style: str = Field(default="professional", description="Writing style")


class PropertyDescriptionResponse(BaseModel):
    """Property description response."""
    description: str


class SummarizeRequest(BaseModel):
    """Conversation summarization request."""
    messages: list[dict] = Field(..., description="Conversation messages")
    include_sentiment: bool = True


class SummarizeResponse(BaseModel):
    """Conversation summary response."""
    summary: str
    key_points: list[str]
    action_items: list[str]
    sentiment: Optional[str] = None


class EmbeddingRequest(BaseModel):
    """Embedding generation request."""
    text: str = Field(..., min_length=1, max_length=30000)
    model: str = Field(default="text-embedding-3-small")


class EmbeddingResponse(BaseModel):
    """Embedding response."""
    embedding: list[float]
    dimensions: int


# ============================================================
# Endpoints
# ============================================================

@router.post("/chat", response_model=ChatResponse)
async def create_chat_completion(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a chat completion using OpenAI.
    
    Send messages and receive AI-generated responses.
    """
    try:
        response = chat_completion(
            messages=request.messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            system_prompt=request.system_prompt
        )
        
        return ChatResponse(response=response, model=request.model)
        
    except IntegrationError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e.message)
        )


@router.post("/lead-response", response_model=LeadResponseResponse)
async def generate_lead_response_endpoint(
    request: LeadResponseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate an AI response to a lead inquiry.
    
    Uses context about the lead and property to generate
    a personalized, helpful response.
    """
    try:
        lead_context = {}
        if request.lead_name:
            lead_context["name"] = request.lead_name
        if request.lead_interest:
            lead_context["interest"] = request.lead_interest
        
        response = generate_lead_response(
            lead_message=request.lead_message,
            lead_context=lead_context if lead_context else None,
            conversation_history=request.conversation_history,
            property_info=request.property_info
        )
        
        return LeadResponseResponse(response=response)
        
    except IntegrationError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e.message)
        )


@router.post("/property-description", response_model=PropertyDescriptionResponse)
async def generate_property_description_endpoint(
    request: PropertyDescriptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a compelling property listing description.
    
    Creates marketing copy highlighting property features.
    """
    try:
        property_details = {
            "Bedrooms": request.beds,
            "Bathrooms": request.baths,
            "Square Feet": request.sqft,
            "Price": request.price,
        }
        
        if request.amenities:
            property_details["Amenities"] = ", ".join(request.amenities)
        if request.location:
            property_details["Location"] = request.location
        
        description = generate_property_description(
            property_details=property_details,
            style=request.style
        )
        
        return PropertyDescriptionResponse(description=description)
        
    except IntegrationError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e.message)
        )


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_conversation_endpoint(
    request: SummarizeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Summarize a conversation between agent and prospect.
    
    Extracts key points, action items, and sentiment.
    """
    try:
        result = summarize_conversation(
            messages=request.messages,
            include_sentiment=request.include_sentiment
        )
        
        return SummarizeResponse(
            summary=result.get("summary", ""),
            key_points=result.get("key_points", []),
            action_items=result.get("action_items", []),
            sentiment=result.get("sentiment") if request.include_sentiment else None
        )
        
    except IntegrationError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e.message)
        )


@router.post("/embedding", response_model=EmbeddingResponse)
async def generate_embedding_endpoint(
    request: EmbeddingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate an embedding vector for text.
    
    Useful for semantic search and document similarity.
    """
    try:
        embedding = generate_embedding(
            text=request.text,
            model=request.model
        )
        
        return EmbeddingResponse(
            embedding=embedding,
            dimensions=len(embedding)
        )
        
    except IntegrationError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e.message)
        )


@router.get("/status")
async def openai_status(
    current_user: User = Depends(get_current_user)
):
    """
    Check OpenAI integration status.
    """
    from app.integrations.openai.client import get_openai_client
    
    client = get_openai_client()
    
    return {
        "configured": client.is_configured(),
        "models_available": ["gpt-4o", "gpt-3.5-turbo", "text-embedding-3-small"],
        "features": [
            "chat_completion",
            "lead_response",
            "property_description",
            "conversation_summary",
            "embeddings"
        ]
    }

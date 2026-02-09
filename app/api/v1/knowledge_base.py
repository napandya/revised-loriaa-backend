"""Knowledge base endpoints for RAG and vector search."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import UUID
from app.database import get_db
from app.models.user import User
from app.models.bot import Bot
from app.models.knowledge_base import KnowledgeBase
from app.schemas.knowledge_base import (
    DocumentCreate,
    DocumentResponse,
    QueryRequest,
    QueryResult,
    ChatRequest
)
from app.core.embeddings import generate_embedding
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    document: DocumentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new document in the knowledge base with embeddings.
    
    Args:
        document: Document creation data
        current_user: The authenticated user
        db: Database session
        
    Returns:
        The created document
        
    Raises:
        HTTPException: If bot not found or user doesn't have access
    """
    # Verify bot belongs to current user
    bot = db.query(Bot).filter(
        Bot.id == document.bot_id,
        Bot.user_id == current_user.id
    ).first()
    
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    # Generate embedding for the document content
    try:
        embedding = await generate_embedding(document.content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate embedding: {str(e)}"
        )
    
    # Create document
    db_document = KnowledgeBase(
        bot_id=document.bot_id,
        title=document.title,
        content=document.content,
        embedding=embedding,
        document_metadata=document.document_metadata
    )
    
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    
    return db_document


@router.get("/documents", response_model=List[DocumentResponse])
async def get_documents(
    bot_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all documents for a bot.
    
    Args:
        bot_id: Bot UUID
        current_user: The authenticated user
        db: Database session
        
    Returns:
        List of documents
        
    Raises:
        HTTPException: If bot not found or user doesn't have access
    """
    # Verify bot belongs to current user
    bot = db.query(Bot).filter(
        Bot.id == bot_id,
        Bot.user_id == current_user.id
    ).first()
    
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    documents = db.query(KnowledgeBase).filter(
        KnowledgeBase.bot_id == bot_id
    ).all()
    
    return documents


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a document from the knowledge base.
    
    Args:
        doc_id: Document UUID
        current_user: The authenticated user
        db: Database session
        
    Raises:
        HTTPException: If document not found or user doesn't have access
    """
    document = db.query(KnowledgeBase).filter(KnowledgeBase.id == doc_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Verify bot belongs to current user
    bot = db.query(Bot).filter(
        Bot.id == document.bot_id,
        Bot.user_id == current_user.id
    ).first()
    
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    db.delete(document)
    db.commit()


@router.post("/query", response_model=List[QueryResult])
async def query_knowledge_base(
    query: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Query knowledge base using vector similarity search.
    
    Args:
        query: Query request with bot ID and query text
        current_user: The authenticated user
        db: Database session
        
    Returns:
        List of similar documents
        
    Raises:
        HTTPException: If bot not found or user doesn't have access
    """
    # Verify bot belongs to current user
    bot = db.query(Bot).filter(
        Bot.id == query.bot_id,
        Bot.user_id == current_user.id
    ).first()
    
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    # Generate embedding for the query
    try:
        query_embedding = await generate_embedding(query.query)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate query embedding: {str(e)}"
        )
    
    # Perform vector similarity search using pgvector
    # Using cosine distance operator <=>
    sql = text("""
        SELECT id, title, content, document_metadata, 
               1 - (embedding <=> :query_embedding) as similarity_score
        FROM knowledge_base
        WHERE bot_id = :bot_id
        ORDER BY embedding <=> :query_embedding
        LIMIT :top_k
    """)
    
    result = db.execute(
        sql,
        {
            "query_embedding": str(query_embedding),
            "bot_id": str(query.bot_id),
            "top_k": query.top_k
        }
    )
    
    results = []
    for row in result:
        results.append(QueryResult(
            document_id=row.id,
            title=row.title,
            content=row.content,
            similarity_score=float(row.similarity_score),
            document_metadata=row.document_metadata
        ))
    
    return results


@router.post("/chat")
async def chat_with_knowledge_base(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """RAG-based chat with knowledge base.
    
    Args:
        chat_request: Chat request with message and conversation history
        current_user: The authenticated user
        db: Database session
        
    Returns:
        Chat response with context from knowledge base
        
    Raises:
        HTTPException: If bot not found or user doesn't have access
    """
    # Verify bot belongs to current user
    bot = db.query(Bot).filter(
        Bot.id == chat_request.bot_id,
        Bot.user_id == current_user.id
    ).first()
    
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    # Query knowledge base for relevant context
    query_req = QueryRequest(
        bot_id=chat_request.bot_id,
        query=chat_request.message,
        top_k=3
    )
    
    relevant_docs = await query_knowledge_base(query_req, current_user, db)
    
    # Build context from relevant documents
    context = "\n\n".join([
        f"Document: {doc.title}\n{doc.content}"
        for doc in relevant_docs
    ])
    
    # Return context and message for frontend to use with OpenAI
    return {
        "message": chat_request.message,
        "context": context,
        "relevant_documents": [
            {
                "title": doc.title,
                "similarity_score": doc.similarity_score
            }
            for doc in relevant_docs
        ]
    }

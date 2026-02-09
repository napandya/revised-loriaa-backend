"""Document management API endpoints for knowledge base and RAG."""

from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.document import DocumentCategory
from app.schemas.document import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentQuery,
    DocumentSearchResult,
)
from app.services.document_service import (
    create_document,
    get_document,
    get_documents,
    update_document,
    delete_document,
    search_documents,
    query_documents,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    category: Optional[DocumentCategory] = None,
    property_id: Optional[UUID] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List documents with optional filters."""
    filters = {}
    if category:
        filters['category'] = category
    if property_id:
        filters['property_id'] = property_id
    if search:
        filters['search'] = search
    
    documents = get_documents(
        db=db,
        user_id=current_user.id,
        filters=filters,
        skip=skip,
        limit=limit
    )
    return documents


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_new_document(
    document_data: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload/create a document."""
    document = create_document(db=db, document_data=document_data)
    return document


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document_details(
    doc_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get document details."""
    document = get_document(db=db, document_id=doc_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    return document


@router.put("/{doc_id}", response_model=DocumentResponse)
async def update_document_details(
    doc_id: UUID,
    document_data: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update document."""
    document = update_document(
        db=db,
        document_id=doc_id,
        document_data=document_data
    )
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    return document


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_by_id(
    doc_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete document."""
    success = delete_document(db=db, document_id=doc_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    return None


@router.post("/search", response_model=List[DocumentSearchResult])
async def search_documents_rag(
    query: DocumentQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search documents with RAG similarity search."""
    results = search_documents(
        db=db,
        query=query.query,
        user_id=current_user.id,
        property_id=query.property_id,
        category=query.category,
        top_k=query.top_k
    )
    return results


@router.post("/query")
async def query_documents_nlp(
    query: DocumentQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Natural language Q&A over documents."""
    answer = query_documents(
        db=db,
        query=query.query,
        user_id=current_user.id,
        property_id=query.property_id,
        category=query.category
    )
    return {"query": query.query, "answer": answer}

"""Document and RAG tools for agents."""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import logging

from app.services.document_service import DocumentService

logger = logging.getLogger(__name__)

# Initialize document service (singleton pattern)
_document_service = None


def _get_document_service(db: Session) -> DocumentService:
    """Get or create document service instance."""
    global _document_service
    if _document_service is None:
        _document_service = DocumentService(db)
    return _document_service


def search_knowledge_base(
    query: str,
    property_id: str = None,
    db: Session = None,
    limit: int = 5
) -> Dict[str, Any]:
    """
    Search the knowledge base for relevant documents.
    
    Args:
        query: Search query
        property_id: Optional property ID to filter by
        db: Database session
        limit: Maximum number of results
    
    Returns:
        Dict with search results
    """
    try:
        if not db:
            return {"error": "Database session required"}
        
        service = _get_document_service(db)
        
        # Perform semantic search
        results = service.search_documents(
            query=query,
            property_id=property_id,
            limit=limit
        )
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "count": len(results),
            "property_id": property_id
        }
        
    except Exception as e:
        logger.error(f"Error searching knowledge base: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "query": query
        }


def get_document(doc_id: str, db: Session) -> Dict[str, Any]:
    """
    Get a specific document by ID.
    
    Args:
        doc_id: Document ID
        db: Database session
    
    Returns:
        Dict with document details
    """
    try:
        service = _get_document_service(db)
        document = service.get_document(doc_id)
        
        if not document:
            return {
                "success": False,
                "error": f"Document {doc_id} not found"
            }
        
        return {
            "success": True,
            "id": str(document.id),
            "title": document.title,
            "content": document.content,
            "document_type": document.document_type,
            "property_id": str(document.property_id) if document.property_id else None,
            "metadata": document.extra_data,
            "created_at": document.created_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting document: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "doc_id": doc_id
        }


def answer_question(
    question: str,
    property_id: str = None,
    db: Session = None,
    context_limit: int = 3
) -> Dict[str, Any]:
    """
    Answer a question using RAG (Retrieval Augmented Generation).
    
    Args:
        question: The question to answer
        property_id: Optional property ID for context
        db: Database session
        context_limit: Number of context documents to retrieve
    
    Returns:
        Dict with answer and sources
    """
    try:
        if not db:
            return {"error": "Database session required"}
        
        # Search for relevant context
        search_results = search_knowledge_base(
            query=question,
            property_id=property_id,
            db=db,
            limit=context_limit
        )
        
        if not search_results.get("success"):
            return search_results
        
        results = search_results.get("results", [])
        
        if not results:
            return {
                "success": True,
                "answer": "I don't have enough information to answer that question. Please consult your property management documentation or contact your supervisor.",
                "sources": [],
                "confidence": "low"
            }
        
        # Build context from results
        context_parts = []
        sources = []
        
        for i, result in enumerate(results):
            context_parts.append(f"[Source {i+1}] {result.get('content', '')}")
            sources.append({
                "title": result.get("title"),
                "doc_id": result.get("id"),
                "relevance_score": result.get("score")
            })
        
        context = "\n\n".join(context_parts)
        
        # Use document service to generate answer
        service = _get_document_service(db)
        answer = service.generate_answer(question, context)
        
        return {
            "success": True,
            "question": question,
            "answer": answer,
            "sources": sources,
            "confidence": "high" if len(results) >= 2 else "medium",
            "property_id": property_id
        }
        
    except Exception as e:
        logger.error(f"Error answering question: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "question": question
        }


def list_documents(
    property_id: str = None,
    document_type: str = None,
    db: Session = None,
    limit: int = 20
) -> Dict[str, Any]:
    """
    List available documents.
    
    Args:
        property_id: Optional property ID filter
        document_type: Optional document type filter
        db: Database session
        limit: Maximum number of results
    
    Returns:
        Dict with document list
    """
    try:
        if not db:
            return {"error": "Database session required"}
        
        service = _get_document_service(db)
        documents = service.list_documents(
            property_id=property_id,
            document_type=document_type,
            limit=limit
        )
        
        doc_list = [
            {
                "id": str(doc.id),
                "title": doc.title,
                "document_type": doc.document_type,
                "property_id": str(doc.property_id) if doc.property_id else None,
                "created_at": doc.created_at.isoformat()
            }
            for doc in documents
        ]
        
        return {
            "success": True,
            "documents": doc_list,
            "count": len(doc_list),
            "filters": {
                "property_id": property_id,
                "document_type": document_type
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

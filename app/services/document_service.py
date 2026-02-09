"""Document processing service with AI embeddings and semantic search."""

from typing import List, Optional, Dict, Any
from uuid import UUID
import openai
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.document import Document, DocumentCategory
from app.schemas.document import DocumentCreate, DocumentResponse, DocumentUpdate
from app.core.config import settings
from app.core.exceptions import NotFoundError, IntegrationError, DatabaseError, ValidationError


class DocumentService:
    """Document service class wrapper for agent tools."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def search_documents(
        self,
        query: str,
        property_id: Optional[str] = None,
        category: Optional[DocumentCategory] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search documents using semantic similarity."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        prop_uuid = UUID(property_id) if property_id else None
        return loop.run_until_complete(
            search_documents(self.db, query, prop_uuid, category, None, limit)
        )
    
    def get_document(self, document_id: str) -> Document:
        """Get a document by ID."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            get_document(self.db, UUID(document_id))
        )
    
    def create_document(
        self,
        title: str,
        content: str,
        category: DocumentCategory,
        property_id: Optional[str] = None,
        user_id: Optional[str] = None,
        file_url: Optional[str] = None
    ) -> Document:
        """Create a new document."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        prop_uuid = UUID(property_id) if property_id else None
        user_uuid = UUID(user_id) if user_id else None
        
        return loop.run_until_complete(
            create_document(self.db, title, content, category, prop_uuid, user_uuid, file_url)
        )


async def create_document(
    db: Session,
    title: str,
    content: str,
    category: DocumentCategory,
    property_id: Optional[UUID],
    user_id: UUID,
    file_url: Optional[str] = None
) -> Document:
    """
    Create a new document with AI embeddings.
    
    Args:
        db: Database session
        title: Document title
        content: Document content/text
        category: Document category
        property_id: Associated property (optional)
        user_id: User creating the document
        file_url: Optional file URL if uploaded
        
    Returns:
        Created document instance
        
    Raises:
        IntegrationError: If embedding generation fails
        DatabaseError: If database operation fails
    """
    try:
        # Generate embedding for the content
        embedding = await generate_embedding(content)
        
        # Create document
        document = Document(
            user_id=user_id,
            property_id=property_id,
            title=title,
            content=content,
            category=category,
            file_url=file_url,
            embedding=embedding
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        return document
        
    except IntegrationError:
        raise
    except Exception as e:
        db.rollback()
        raise DatabaseError(f"Failed to create document: {str(e)}")


async def generate_embedding(text: str) -> List[float]:
    """
    Generate OpenAI embeddings for text content.
    
    Uses OpenAI's text-embedding-ada-002 model to generate 1536-dimensional
    embeddings for semantic search.
    
    Args:
        text: Text to embed
        
    Returns:
        List of 1536 floats representing the embedding vector
        
    Raises:
        IntegrationError: If OpenAI API call fails
        ValidationError: If text is empty
    """
    if not text or not text.strip():
        raise ValidationError("Text cannot be empty for embedding generation")
    
    if not settings.OPENAI_API_KEY:
        raise IntegrationError(
            "OpenAI API key not configured",
            "OpenAI",
            {"detail": "OPENAI_API_KEY environment variable not set"}
        )
    
    try:
        # Configure OpenAI client
        openai.api_key = settings.OPENAI_API_KEY
        
        # Truncate text if too long (max 8191 tokens for ada-002)
        # Rough estimate: 1 token ~= 4 characters
        max_chars = 30000
        if len(text) > max_chars:
            text = text[:max_chars]
        
        # Generate embedding
        response = openai.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        
        embedding = response.data[0].embedding
        
        # Validate embedding dimension
        if len(embedding) != 1536:
            raise IntegrationError(
                f"Unexpected embedding dimension: {len(embedding)}",
                "OpenAI",
                {"expected": 1536, "received": len(embedding)}
            )
        
        return embedding
        
    except openai.APIError as e:
        raise IntegrationError(
            f"OpenAI API error: {str(e)}",
            "OpenAI",
            {"error_type": type(e).__name__}
        )
    except openai.AuthenticationError:
        raise IntegrationError(
            "OpenAI authentication failed - invalid API key",
            "OpenAI"
        )
    except openai.RateLimitError:
        raise IntegrationError(
            "OpenAI rate limit exceeded",
            "OpenAI",
            {"retry_after": "60"}
        )
    except Exception as e:
        raise IntegrationError(
            f"Failed to generate embedding: {str(e)}",
            "OpenAI"
        )


async def search_documents(
    db: Session,
    query: str,
    property_id: Optional[UUID] = None,
    category: Optional[DocumentCategory] = None,
    user_id: Optional[UUID] = None,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Semantic search for documents using cosine similarity.
    
    Generates an embedding for the query and finds the most similar documents
    using pgvector's cosine distance operator.
    
    Args:
        db: Database session
        query: Search query text
        property_id: Filter by property (optional)
        category: Filter by category (optional)
        user_id: Filter by user (optional)
        top_k: Number of results to return
        
    Returns:
        List of documents with similarity scores
        
    Raises:
        IntegrationError: If embedding generation fails
        DatabaseError: If search query fails
    """
    try:
        # Generate embedding for query
        query_embedding = await generate_embedding(query)
        
        # Build SQL query with pgvector cosine distance
        # Use <=> operator for cosine distance (lower is more similar)
        sql_query = text("""
            SELECT 
                id,
                user_id,
                property_id,
                title,
                content,
                category,
                file_url,
                created_at,
                updated_at,
                (embedding <=> CAST(:query_embedding AS vector)) as distance
            FROM documents
            WHERE 1=1
                AND (:property_id IS NULL OR property_id = :property_id)
                AND (:category IS NULL OR category = :category)
                AND (:user_id IS NULL OR user_id = :user_id)
            ORDER BY embedding <=> CAST(:query_embedding AS vector)
            LIMIT :limit
        """)
        
        # Execute query
        result = db.execute(
            sql_query,
            {
                "query_embedding": str(query_embedding),
                "property_id": str(property_id) if property_id else None,
                "category": category.value if category else None,
                "user_id": str(user_id) if user_id else None,
                "limit": top_k
            }
        )
        
        # Format results
        documents = []
        for row in result:
            # Calculate similarity score (1 - cosine_distance)
            similarity_score = 1 - row.distance if row.distance is not None else 0.0
            
            documents.append({
                "id": str(row.id),
                "title": row.title,
                "content": row.content[:500] + "..." if len(row.content) > 500 else row.content,
                "category": row.category,
                "file_url": row.file_url,
                "similarity_score": round(similarity_score, 4),
                "created_at": row.created_at.isoformat() if row.created_at else None
            })
        
        return documents
        
    except IntegrationError:
        raise
    except Exception as e:
        raise DatabaseError(f"Failed to search documents: {str(e)}")


async def get_document(db: Session, document_id: UUID) -> Document:
    """
    Get a document by ID.
    
    Args:
        db: Database session
        document_id: Document UUID
        
    Returns:
        Document instance
        
    Raises:
        NotFoundError: If document not found
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise NotFoundError(f"Document with ID {document_id} not found", "Document")
    return document


async def delete_document(db: Session, doc_id: UUID) -> Dict[str, Any]:
    """
    Delete a document.
    
    Args:
        db: Database session
        doc_id: Document UUID
        
    Returns:
        Success status dictionary
        
    Raises:
        NotFoundError: If document not found
        DatabaseError: If deletion fails
    """
    try:
        document = db.query(Document).filter(Document.id == doc_id).first()
        if not document:
            raise NotFoundError(f"Document with ID {doc_id} not found", "Document")
        
        # Store title for response
        title = document.title
        
        # Delete document
        db.delete(document)
        db.commit()
        
        return {
            "success": True,
            "document_id": str(doc_id),
            "title": title,
            "message": "Document deleted successfully"
        }
        
    except NotFoundError:
        raise
    except Exception as e:
        db.rollback()
        raise DatabaseError(f"Failed to delete document: {str(e)}")


async def list_documents(
    db: Session,
    property_id: Optional[UUID] = None,
    category: Optional[DocumentCategory] = None,
    user_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 50
) -> List[Document]:
    """
    List documents with optional filters.
    
    Args:
        db: Database session
        property_id: Filter by property
        category: Filter by category
        user_id: Filter by user
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of documents
    """
    query = db.query(Document)
    
    if property_id:
        query = query.filter(Document.property_id == property_id)
    if category:
        query = query.filter(Document.category == category)
    if user_id:
        query = query.filter(Document.user_id == user_id)
    
    query = query.order_by(Document.created_at.desc())
    return query.offset(skip).limit(limit).all()


def get_documents(
    db: Session,
    user_id: Optional[UUID] = None,
    filters: Optional[Dict[str, Any]] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Document]:
    """
    Get documents with filters (synchronous version for API).
    
    Args:
        db: Database session
        user_id: Filter by user
        filters: Optional dictionary of filters (category, property_id, search)
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of documents
    """
    query = db.query(Document)
    
    if user_id:
        query = query.filter(Document.user_id == user_id)
    
    if filters:
        if filters.get('category'):
            query = query.filter(Document.category == filters['category'])
        if filters.get('property_id'):
            query = query.filter(Document.property_id == filters['property_id'])
        if filters.get('search'):
            search_term = f"%{filters['search']}%"
            query = query.filter(
                (Document.title.ilike(search_term)) |
                (Document.content.ilike(search_term))
            )
    
    query = query.order_by(Document.created_at.desc())
    return query.offset(skip).limit(limit).all()


def update_document(
    db: Session,
    document_id: UUID,
    document_data: DocumentUpdate
) -> Optional[Document]:
    """
    Update a document.
    
    Args:
        db: Database session
        document_id: Document UUID
        document_data: Update data
        
    Returns:
        Updated document or None if not found
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        return None
    
    update_data = document_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(document, field, value)
    
    db.commit()
    db.refresh(document)
    return document


def query_documents(
    db: Session,
    query: str,
    user_id: Optional[UUID] = None,
    property_id: Optional[UUID] = None,
    category: Optional[DocumentCategory] = None
) -> str:
    """
    Natural language Q&A over documents using RAG.
    
    Args:
        db: Database session
        query: User question
        user_id: Filter by user
        property_id: Filter by property
        category: Filter by category
        
    Returns:
        AI-generated answer based on relevant documents
    """
    import asyncio
    
    # Get relevant documents using semantic search
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        results = loop.run_until_complete(
            search_documents(db, query, property_id, category, user_id, top_k=3)
        )
    except Exception:
        results = []
    
    if not results:
        return "I couldn't find any relevant documents to answer your question. Please try a different query or upload relevant documents."
    
    # Build context from search results
    context_parts = []
    for doc in results:
        context_parts.append(f"Document: {doc['title']}\nContent: {doc['content']}")
    
    context = "\n\n".join(context_parts)
    
    # Generate answer using OpenAI
    if not settings.OPENAI_API_KEY:
        return f"Based on the documents found, here are the relevant excerpts:\n\n{context}"
    
    try:
        import openai
        openai.api_key = settings.OPENAI_API_KEY
        
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that answers questions based on the provided document context. Only use information from the context to answer. If the context doesn't contain relevant information, say so."
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {query}"
                }
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Based on the documents found, here are the relevant excerpts:\n\n{context}"

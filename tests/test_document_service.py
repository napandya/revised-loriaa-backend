"""
Unit tests for Document Service.
"""

import pytest
from uuid import uuid4
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentCategory
from app.models.user import User
from app.models.bot import Bot
from app.services.document_service import (
    get_documents,
    update_document,
)
from app.schemas.document import DocumentUpdate


class TestGetDocuments:
    """Tests for get_documents function."""
    
    def test_get_documents_returns_list(self, db: Session, test_user: User, test_document: Document):
        """Test that get_documents returns a list."""
        documents = get_documents(db, user_id=test_user.id)
        assert isinstance(documents, list)
        assert len(documents) >= 1
    
    def test_get_documents_filters_by_category(self, db: Session, test_user: User, test_document: Document):
        """Test filtering documents by category."""
        documents = get_documents(
            db,
            user_id=test_user.id,
            filters={"category": DocumentCategory.policy}
        )
        assert all(doc.category == DocumentCategory.policy for doc in documents)
    
    def test_get_documents_search(self, db: Session, test_user: User, test_document: Document):
        """Test searching documents by text."""
        documents = get_documents(
            db,
            user_id=test_user.id,
            filters={"search": "test"}
        )
        assert len(documents) >= 1
        assert any("test" in doc.title.lower() or "test" in doc.content.lower() for doc in documents)
    
    def test_get_documents_pagination(self, db: Session, test_user: User, test_bot: Bot):
        """Test pagination of documents."""
        # Create multiple documents
        for i in range(5):
            doc = Document(
                user_id=test_user.id,
                property_id=test_bot.id,
                title=f"Document {i}",
                content=f"Content for document {i}",
                category=DocumentCategory.policy
            )
            db.add(doc)
        db.commit()
        
        # Test pagination
        docs_page1 = get_documents(db, user_id=test_user.id, skip=0, limit=2)
        docs_page2 = get_documents(db, user_id=test_user.id, skip=2, limit=2)
        
        assert len(docs_page1) == 2
        assert len(docs_page2) == 2
    
    def test_get_documents_empty_result(self, db: Session):
        """Test get_documents with no matching results."""
        documents = get_documents(db, user_id=uuid4())
        assert documents == []


class TestUpdateDocument:
    """Tests for update_document function."""
    
    def test_update_document_title(self, db: Session, test_document: Document):
        """Test updating document title."""
        update_data = DocumentUpdate(title="Updated Title")
        
        updated_doc = update_document(
            db=db,
            document_id=test_document.id,
            document_data=update_data
        )
        
        assert updated_doc is not None
        assert updated_doc.title == "Updated Title"
    
    def test_update_document_content(self, db: Session, test_document: Document):
        """Test updating document content."""
        update_data = DocumentUpdate(content="Updated content here.")
        
        updated_doc = update_document(
            db=db,
            document_id=test_document.id,
            document_data=update_data
        )
        
        assert updated_doc is not None
        assert updated_doc.content == "Updated content here."
    
    def test_update_document_category(self, db: Session, test_document: Document):
        """Test updating document category."""
        update_data = DocumentUpdate(category=DocumentCategory.faq)
        
        updated_doc = update_document(
            db=db,
            document_id=test_document.id,
            document_data=update_data
        )
        
        assert updated_doc is not None
        assert updated_doc.category == DocumentCategory.faq
    
    def test_update_document_not_found(self, db: Session):
        """Test updating non-existent document."""
        update_data = DocumentUpdate(title="New Title")
        
        result = update_document(
            db=db,
            document_id=uuid4(),
            document_data=update_data
        )
        
        assert result is None


class TestDocumentCategories:
    """Tests for document category handling."""
    
    def test_all_categories_supported(self, db: Session, test_user: User, test_bot: Bot):
        """Test that all document categories are supported."""
        categories = [
            DocumentCategory.policy,
            DocumentCategory.procedure,
            DocumentCategory.faq,
            DocumentCategory.training
        ]
        
        for category in categories:
            doc = Document(
                user_id=test_user.id,
                property_id=test_bot.id,
                title=f"{category.value} Document",
                content=f"Content for {category.value}",
                category=category
            )
            db.add(doc)
        
        db.commit()
        
        # Verify each category can be retrieved
        for category in categories:
            docs = get_documents(
                db,
                user_id=test_user.id,
                filters={"category": category}
            )
            assert len(docs) >= 1

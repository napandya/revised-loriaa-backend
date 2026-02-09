"""
Test configuration and fixtures for Loriaa AI Backend.
"""

import os
import pytest
from typing import Generator, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

# Set test environment
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "postgresql://test:test@localhost:5432/loriaa_test")

from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.bot import Bot, BotStatus
from app.models.lead import Lead, LeadSource, LeadStatus
from app.models.conversation import Conversation, ConversationChannel, ConversationStatus
from app.models.message import Message, MessageDirection
from app.models.document import Document, DocumentCategory
from app.models.agent_activity import AgentActivity, AgentType
from app.models.team import TeamMember, TeamRole
from app.models.integration_config import IntegrationConfig, IntegrationName
from app.core.security import get_password_hash, create_access_token


# Test database engine
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "postgresql://test:test@localhost:5432/loriaa_test")
test_engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Override database dependency for tests."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Apply database override
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create test database tables at session start."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Get database session for tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    """Get test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def test_user(db: Session) -> User:
    """Create a test user."""
    user = User(
        email=f"test_{uuid4().hex[:8]}@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_bot(db: Session, test_user: User) -> Bot:
    """Create a test bot (property)."""
    bot = Bot(
        user_id=test_user.id,
        name="Test Property",
        hipaa_compliant=False,
        language="en-US",
        status=BotStatus.active,
        greeting_text="Hello, how can I help?",
        prompt="You are a helpful assistant.",
        voice="Shimmer",
        model="gpt-4o",
        cost_per_minute=0.18
    )
    db.add(bot)
    db.commit()
    db.refresh(bot)
    return bot


@pytest.fixture(scope="function")
def test_lead(db: Session, test_user: User, test_bot: Bot) -> Lead:
    """Create a test lead."""
    lead = Lead(
        property_id=test_bot.id,
        user_id=test_user.id,
        name="Test Lead",
        email="testlead@example.com",
        phone="(555) 123-4567",
        source=LeadSource.website,
        status=LeadStatus.new,
        score=75,
        extra_data={"unit_interest": "2 Bed", "ai_insight": "Test insight"}
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@pytest.fixture(scope="function")
def test_conversation(db: Session, test_lead: Lead) -> Conversation:
    """Create a test conversation."""
    conv = Conversation(
        lead_id=test_lead.id,
        channel=ConversationChannel.sms,
        status=ConversationStatus.open,
        last_message_at=datetime.utcnow()
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


@pytest.fixture(scope="function")
def test_message(db: Session, test_conversation: Conversation) -> Message:
    """Create a test message."""
    msg = Message(
        conversation_id=test_conversation.id,
        direction=MessageDirection.inbound,
        content="Test message content",
        sender="Test Lead",
        recipient="System"
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


@pytest.fixture(scope="function")
def test_document(db: Session, test_user: User, test_bot: Bot) -> Document:
    """Create a test document."""
    doc = Document(
        user_id=test_user.id,
        property_id=test_bot.id,
        title="Test Document",
        content="This is test document content for testing purposes.",
        category=DocumentCategory.policy
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@pytest.fixture(scope="function")
def auth_headers(test_user: User) -> Dict[str, str]:
    """Generate authentication headers for test user."""
    token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def sample_lead_data(test_user: User, test_bot: Bot) -> Dict[str, Any]:
    """Sample lead creation data."""
    return {
        "property_id": str(test_bot.id),
        "user_id": str(test_user.id),
        "name": "Sample Lead",
        "email": "sample@example.com",
        "phone": "(555) 987-6543",
        "source": "website",
        "status": "new"
    }


@pytest.fixture(scope="function")
def sample_document_data(test_user: User, test_bot: Bot) -> Dict[str, Any]:
    """Sample document creation data."""
    return {
        "user_id": str(test_user.id),
        "property_id": str(test_bot.id),
        "title": "Sample Policy",
        "content": "This is a sample policy document.",
        "category": "policy"
    }

"""
Integration tests for API endpoints.
"""

import pytest
from typing import Dict
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.lead import Lead
from app.models.conversation import Conversation
from app.models.document import Document


class TestAuthEndpoints:
    """Integration tests for authentication endpoints."""
    
    def test_login_success(self, client: TestClient, test_user: User):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": test_user.email, "password": "testpassword123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client: TestClient):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "wrong@email.com", "password": "wrongpassword"}
        )
        assert response.status_code == 401
    
    def test_get_current_user(self, client: TestClient, auth_headers: Dict[str, str], test_user: User):
        """Test getting current user info."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
    
    def test_get_current_user_unauthorized(self, client: TestClient):
        """Test accessing protected route without auth."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401


class TestLeadsEndpoints:
    """Integration tests for leads endpoints."""
    
    def test_list_leads(self, client: TestClient, auth_headers: Dict[str, str], test_lead: Lead):
        """Test listing leads."""
        response = client.get("/api/v1/leads", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_leads_with_filters(self, client: TestClient, auth_headers: Dict[str, str], test_lead: Lead):
        """Test listing leads with status filter."""
        response = client.get("/api/v1/leads?status=new", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert all(lead.get("status") == "new" for lead in data if "status" in lead)
    
    def test_get_lead_detail(self, client: TestClient, auth_headers: Dict[str, str], test_lead: Lead):
        """Test getting lead details."""
        response = client.get(f"/api/v1/leads/{test_lead.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_lead.id)
    
    def test_get_lead_not_found(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test getting non-existent lead."""
        import uuid
        response = client.get(f"/api/v1/leads/{uuid.uuid4()}", headers=auth_headers)
        assert response.status_code == 404
    
    def test_update_lead_status(self, client: TestClient, auth_headers: Dict[str, str], test_lead: Lead):
        """Test updating lead status."""
        response = client.patch(
            f"/api/v1/leads/{test_lead.id}/status?new_status=contacted",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "contacted"
    
    def test_get_pipeline_stats(self, client: TestClient, auth_headers: Dict[str, str], test_lead: Lead):
        """Test getting pipeline statistics."""
        response = client.get("/api/v1/leads/pipeline/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_leads" in data
        assert "conversion_rate" in data


class TestInboxEndpoints:
    """Integration tests for inbox endpoints."""
    
    def test_list_conversations(self, client: TestClient, auth_headers: Dict[str, str], test_conversation: Conversation):
        """Test listing conversations."""
        response = client.get("/api/v1/inbox", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_conversations_with_channel_filter(self, client: TestClient, auth_headers: Dict[str, str], test_conversation: Conversation):
        """Test listing conversations with channel filter."""
        response = client.get("/api/v1/inbox?channel=sms", headers=auth_headers)
        assert response.status_code == 200
    
    def test_get_conversation_detail(self, client: TestClient, auth_headers: Dict[str, str], test_conversation: Conversation):
        """Test getting conversation with messages."""
        response = client.get(f"/api/v1/inbox/{test_conversation.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_conversation.id)
    
    def test_send_message(self, client: TestClient, auth_headers: Dict[str, str], test_conversation: Conversation):
        """Test sending a message."""
        response = client.post(
            f"/api/v1/inbox/{test_conversation.id}/messages?content=Hello%20test",
            headers=auth_headers
        )
        assert response.status_code == 201
    
    def test_get_unread_count(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test getting unread message count."""
        response = client.get("/api/v1/inbox/unread/count", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "unread_count" in data


class TestDocumentsEndpoints:
    """Integration tests for documents endpoints."""
    
    def test_list_documents(self, client: TestClient, auth_headers: Dict[str, str], test_document: Document):
        """Test listing documents."""
        response = client.get("/api/v1/documents", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_documents_with_category_filter(self, client: TestClient, auth_headers: Dict[str, str], test_document: Document):
        """Test listing documents with category filter."""
        response = client.get("/api/v1/documents?category=policy", headers=auth_headers)
        assert response.status_code == 200
    
    def test_get_document_detail(self, client: TestClient, auth_headers: Dict[str, str], test_document: Document):
        """Test getting document details."""
        response = client.get(f"/api/v1/documents/{test_document.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_document.id)
    
    def test_get_document_not_found(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test getting non-existent document."""
        import uuid
        response = client.get(f"/api/v1/documents/{uuid.uuid4()}", headers=auth_headers)
        assert response.status_code == 404


class TestDashboardEndpoints:
    """Integration tests for dashboard endpoints."""
    
    def test_get_metrics(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test getting dashboard metrics."""
        response = client.get("/api/v1/dashboard/metrics", headers=auth_headers)
        assert response.status_code == 200
    
    def test_get_portfolio_health(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test getting portfolio health."""
        response = client.get("/api/v1/dashboard/portfolio-health", headers=auth_headers)
        assert response.status_code == 200


class TestAgentEndpoints:
    """Integration tests for agent endpoints."""
    
    def test_leasing_agent_activity(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test getting leasing agent activity."""
        response = client.get("/api/v1/agents/leasing/activity", headers=auth_headers)
        assert response.status_code == 200
    
    def test_marketing_agent_activity(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test getting marketing agent activity."""
        response = client.get("/api/v1/agents/marketing/activity", headers=auth_headers)
        assert response.status_code == 200
    
    def test_property_agent_activity(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test getting property manager activity."""
        response = client.get("/api/v1/agents/property/activity", headers=auth_headers)
        assert response.status_code == 200


class TestSettingsEndpoints:
    """Integration tests for settings endpoints."""
    
    def test_get_integrations(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test getting integrations."""
        response = client.get("/api/v1/settings/integrations", headers=auth_headers)
        assert response.status_code == 200
    
    def test_get_profile(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test getting user profile."""
        response = client.get("/api/v1/settings/profile", headers=auth_headers)
        assert response.status_code == 200


class TestHealthEndpoint:
    """Integration tests for health endpoint."""
    
    def test_health_check(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

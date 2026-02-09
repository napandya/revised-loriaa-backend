"""
Unit tests for Lead Service.
"""

import pytest
from uuid import uuid4
from sqlalchemy.orm import Session

from app.models.lead import Lead, LeadSource, LeadStatus
from app.models.user import User
from app.models.bot import Bot
from app.services.lead_service import (
    get_leads,
    delete_lead,
    add_lead_activity,
    calculate_lead_score_internal,
)


class TestGetLeads:
    """Tests for get_leads function."""
    
    def test_get_leads_returns_list(self, db: Session, test_user: User, test_lead: Lead):
        """Test that get_leads returns a list."""
        leads = get_leads(db, user_id=test_user.id)
        assert isinstance(leads, list)
        assert len(leads) >= 1
    
    def test_get_leads_filters_by_status(self, db: Session, test_user: User, test_lead: Lead):
        """Test filtering leads by status."""
        leads = get_leads(db, user_id=test_user.id, filters={"status": LeadStatus.new})
        assert all(lead.status == LeadStatus.new for lead in leads)
    
    def test_get_leads_filters_by_source(self, db: Session, test_user: User, test_lead: Lead):
        """Test filtering leads by source."""
        leads = get_leads(db, user_id=test_user.id, filters={"source": LeadSource.website})
        assert all(lead.source == LeadSource.website for lead in leads)
    
    def test_get_leads_pagination(self, db: Session, test_user: User, test_bot: Bot):
        """Test pagination of leads."""
        # Create multiple leads
        for i in range(5):
            lead = Lead(
                property_id=test_bot.id,
                user_id=test_user.id,
                name=f"Lead {i}",
                email=f"lead{i}@example.com",
                source=LeadSource.website,
                status=LeadStatus.new,
                score=50
            )
            db.add(lead)
        db.commit()
        
        # Test pagination
        leads_page1 = get_leads(db, user_id=test_user.id, skip=0, limit=2)
        leads_page2 = get_leads(db, user_id=test_user.id, skip=2, limit=2)
        
        assert len(leads_page1) == 2
        assert len(leads_page2) == 2
        assert leads_page1[0].id != leads_page2[0].id
    
    def test_get_leads_empty_result(self, db: Session):
        """Test get_leads with no matching results."""
        leads = get_leads(db, user_id=uuid4())
        assert leads == []


class TestDeleteLead:
    """Tests for delete_lead function."""
    
    def test_delete_lead_success(self, db: Session, test_lead: Lead):
        """Test successful lead deletion."""
        lead_id = test_lead.id
        result = delete_lead(db, lead_id)
        
        assert result is True
        assert db.query(Lead).filter(Lead.id == lead_id).first() is None
    
    def test_delete_lead_not_found(self, db: Session):
        """Test deleting non-existent lead."""
        result = delete_lead(db, uuid4())
        assert result is False


class TestAddLeadActivity:
    """Tests for add_lead_activity function."""
    
    def test_add_activity_success(self, db: Session, test_lead: Lead, test_user: User):
        """Test adding activity to lead."""
        activity = add_lead_activity(
            db=db,
            lead_id=test_lead.id,
            activity_type="note",
            description="Test activity",
            metadata={"test": "data"},
            user_id=test_user.id
        )
        
        assert activity is not None
        assert activity.description == "Test activity"
    
    def test_add_activity_lead_not_found(self, db: Session, test_user: User):
        """Test adding activity to non-existent lead."""
        activity = add_lead_activity(
            db=db,
            lead_id=uuid4(),
            activity_type="note",
            description="Test"
        )
        assert activity is None


class TestCalculateLeadScore:
    """Tests for lead score calculation."""
    
    def test_score_referral_source(self, test_lead: Lead):
        """Test that referral source gives highest score."""
        test_lead.source = LeadSource.referral
        test_lead.status = LeadStatus.new
        score_referral = calculate_lead_score_internal(test_lead, 0)
        
        test_lead.source = LeadSource.facebook_ads
        score_fb = calculate_lead_score_internal(test_lead, 0)
        
        assert score_referral > score_fb
    
    def test_score_increases_with_status_progression(self, test_lead: Lead):
        """Test that score increases as lead progresses."""
        test_lead.source = LeadSource.website
        
        test_lead.status = LeadStatus.new
        score_new = calculate_lead_score_internal(test_lead, 0)
        
        test_lead.status = LeadStatus.touring
        score_touring = calculate_lead_score_internal(test_lead, 0)
        
        test_lead.status = LeadStatus.lease
        score_lease = calculate_lead_score_internal(test_lead, 0)
        
        assert score_new < score_touring < score_lease
    
    def test_score_increases_with_engagement(self, test_lead: Lead):
        """Test that score increases with activity count."""
        test_lead.status = LeadStatus.new
        
        score_no_activity = calculate_lead_score_internal(test_lead, 0)
        score_some_activity = calculate_lead_score_internal(test_lead, 5)
        score_high_activity = calculate_lead_score_internal(test_lead, 10)
        
        assert score_no_activity < score_some_activity < score_high_activity
    
    def test_score_max_100(self, test_lead: Lead):
        """Test that score is capped at 100."""
        test_lead.source = LeadSource.referral
        test_lead.status = LeadStatus.lease
        test_lead.email = "test@test.com"
        test_lead.phone = "1234567890"
        
        score = calculate_lead_score_internal(test_lead, 20)
        assert score <= 100

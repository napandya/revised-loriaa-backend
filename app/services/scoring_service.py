"""AI-powered lead scoring service using OpenAI GPT-4o."""

from typing import Dict, Any
from openai import OpenAI
from datetime import datetime, timedelta

from app.models.lead import Lead, LeadSource, LeadStatus
from app.models.lead_activity import LeadActivity
from app.core.config import settings
from app.core.exceptions import IntegrationError
from sqlalchemy.orm import Session


def calculate_lead_score(db: Session, lead: Lead) -> Dict[str, Any]:
    """
    Calculate lead score using OpenAI GPT-4o for intelligent scoring.
    
    Analyzes multiple factors:
    - Lead source quality
    - Engagement level (activities count)
    - Response time patterns
    - Budget indicators from metadata
    - Move-in timeline urgency
    
    Args:
        db: Database session
        lead: Lead instance to score
        
    Returns:
        Dictionary with 'score' (0-100) and 'explanation' describing the reasoning
        
    Raises:
        IntegrationError: If OpenAI API call fails
    """
    try:
        # Check OpenAI API key
        if not settings.OPENAI_API_KEY:
            # Fallback to simple scoring if API key not configured
            return _fallback_scoring(db, lead)
        
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Gather lead data for analysis
        activity_count = db.query(LeadActivity).filter(
            LeadActivity.lead_id == lead.id
        ).count()
        
        # Get recent activities
        recent_activities = db.query(LeadActivity).filter(
            LeadActivity.lead_id == lead.id
        ).order_by(LeadActivity.created_at.desc()).limit(5).all()
        
        # Calculate average response time
        response_times = []
        for i in range(len(recent_activities) - 1):
            time_diff = (recent_activities[i].created_at - recent_activities[i+1].created_at).total_seconds() / 3600
            response_times.append(time_diff)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 24.0
        
        # Build prompt for Gemini
        prompt = f"""
You are a lead scoring expert for a property management company. Analyze this lead and provide a score from 0-100.

Lead Details:
- Name: {lead.name}
- Source: {lead.source.value}
- Current Status: {lead.status.value}
- Contact Info: Email={'Yes' if lead.email else 'No'}, Phone={'Yes' if lead.phone else 'No'}
- Total Activities: {activity_count}
- Average Response Time: {avg_response_time:.1f} hours
- Created: {lead.created_at.strftime('%Y-%m-%d')}
- Days Since Creation: {(datetime.now() - lead.created_at.replace(tzinfo=None)).days}
- Metadata: {lead.extra_data or 'None'}

Scoring Criteria:
1. Lead Source Quality (0-25 points):
   - Referral: 25, Website: 20, Google Ads: 18, Phone: 15, Facebook Ads: 12
   
2. Status Progression (0-25 points):
   - New: 5, Contacted: 10, Qualified: 15, Touring: 20, Application: 22, Lease: 25, Move-in: 25, Lost: 0
   
3. Engagement Level (0-25 points):
   - Based on activities count and recency
   - High activity (10+): 25, Medium (5-9): 18, Low (2-4): 10, Minimal (0-1): 5
   
4. Response Time (0-15 points):
   - Fast (<6 hours): 15, Moderate (6-24 hours): 10, Slow (>24 hours): 5
   
5. Budget & Timeline Indicators from Metadata (0-10 points):
   - Look for budget mentions, move-in dates, urgency signals

Respond ONLY with a JSON object in this exact format:
{{"score": <number 0-100>, "explanation": "<2-3 sentence explanation>"}}
"""
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a lead scoring expert for a property management company. Always respond with valid JSON only."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        response_text = response.choices[0].message.content.strip()
        
        # Parse JSON response
        import json
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()
        
        result = json.loads(response_text)
        
        # Validate score is in range
        score = int(result.get("score", 0))
        score = max(0, min(100, score))
        
        explanation = result.get("explanation", "Score calculated based on lead attributes")
        
        return {
            "score": score,
            "explanation": explanation,
            "scored_at": datetime.now().isoformat(),
            "factors": {
                "activity_count": activity_count,
                "avg_response_time_hours": avg_response_time,
                "days_since_creation": (datetime.now() - lead.created_at.replace(tzinfo=None)).days
            }
        }
        
    except Exception as e:
        # If OpenAI fails, use fallback scoring
        print(f"OpenAI API error: {str(e)}, using fallback scoring")
        return _fallback_scoring(db, lead)


def _fallback_scoring(db: Session, lead: Lead) -> Dict[str, Any]:
    """
    Fallback scoring method when Gemini API is unavailable.
    
    Args:
        db: Database session
        lead: Lead instance
        
    Returns:
        Dictionary with score and explanation
    """
    score = 0
    factors = []
    
    # Get activity count
    activity_count = db.query(LeadActivity).filter(
        LeadActivity.lead_id == lead.id
    ).count()
    
    # Source quality (0-25 points)
    source_scores = {
        LeadSource.referral: 25,
        LeadSource.website: 20,
        LeadSource.google_ads: 18,
        LeadSource.phone: 15,
        LeadSource.facebook_ads: 12
    }
    source_score = source_scores.get(lead.source, 10)
    score += source_score
    factors.append(f"{lead.source.value} source: +{source_score}")
    
    # Status progression (0-25 points)
    status_scores = {
        LeadStatus.new: 5,
        LeadStatus.contacted: 10,
        LeadStatus.qualified: 15,
        LeadStatus.touring: 20,
        LeadStatus.application: 22,
        LeadStatus.lease: 25,
        LeadStatus.move_in: 25,
        LeadStatus.lost: 0
    }
    status_score = status_scores.get(lead.status, 0)
    score += status_score
    factors.append(f"{lead.status.value} status: +{status_score}")
    
    # Engagement level (0-25 points)
    if activity_count >= 10:
        engagement_score = 25
    elif activity_count >= 5:
        engagement_score = 18
    elif activity_count >= 2:
        engagement_score = 10
    else:
        engagement_score = 5
    score += engagement_score
    factors.append(f"{activity_count} activities: +{engagement_score}")
    
    # Contact information (0-15 points)
    contact_score = 0
    if lead.email:
        contact_score += 8
        factors.append("Has email: +8")
    if lead.phone:
        contact_score += 7
        factors.append("Has phone: +7")
    score += contact_score
    
    # Recency boost (0-10 points)
    days_old = (datetime.now() - lead.created_at.replace(tzinfo=None)).days
    if days_old <= 1:
        recency_score = 10
        factors.append("Very recent lead: +10")
    elif days_old <= 7:
        recency_score = 7
        factors.append("Recent lead: +7")
    elif days_old <= 30:
        recency_score = 3
        factors.append("Moderately recent: +3")
    else:
        recency_score = 0
    score += recency_score
    
    score = min(score, 100)
    
    explanation = f"Score based on {len(factors)} factors: " + ", ".join(factors[:3])
    
    return {
        "score": score,
        "explanation": explanation,
        "scored_at": datetime.now().isoformat(),
        "method": "fallback",
        "factors": {
            "activity_count": activity_count,
            "days_since_creation": days_old
        }
    }

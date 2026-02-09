"""Facebook lead form handling."""

from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.exceptions import IntegrationError
from app.models.lead import Lead, LeadSource, LeadStatus
import hashlib
import hmac


async def verify_webhook(
    hub_mode: str,
    hub_challenge: str,
    hub_verify_token: str
) -> Optional[str]:
    """Verify Facebook webhook subscription.
    
    Args:
        hub_mode: Mode from webhook request
        hub_challenge: Challenge token from webhook request
        hub_verify_token: Verify token from webhook request
        
    Returns:
        Challenge string if verification succeeds, None otherwise
    """
    expected_token = settings.FACEBOOK_WEBHOOK_VERIFY_TOKEN
    
    if not expected_token:
        raise IntegrationError(
            message="Facebook webhook verify token not configured",
            integration_name="facebook_ads"
        )
    
    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        return hub_challenge
    
    return None


def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify Facebook webhook signature.
    
    Args:
        payload: Raw request payload
        signature: X-Hub-Signature-256 header value
        
    Returns:
        True if signature is valid, False otherwise
    """
    app_secret = settings.FACEBOOK_APP_SECRET
    
    if not app_secret:
        raise IntegrationError(
            message="Facebook app secret not configured",
            integration_name="facebook_ads"
        )
    
    if not signature or not signature.startswith("sha256="):
        return False
    
    signature_hash = signature.split("=", 1)[1]
    expected_hash = hmac.new(
        app_secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature_hash, expected_hash)


async def process_lead_webhook(
    webhook_data: Dict[str, Any],
    db: AsyncSession
) -> List[Dict[str, Any]]:
    """Process Facebook lead form webhook.
    
    Args:
        webhook_data: Webhook payload from Facebook
        db: Database session
        
    Returns:
        List of processed lead data
    """
    processed_leads = []
    
    for entry in webhook_data.get("entry", []):
        for change in entry.get("changes", []):
            if change.get("field") == "leadgen":
                value = change.get("value", {})
                
                # Extract lead data
                lead_data = {
                    "leadgen_id": value.get("leadgen_id"),
                    "page_id": value.get("page_id"),
                    "form_id": value.get("form_id"),
                    "ad_id": value.get("ad_id"),
                    "adgroup_id": value.get("adgroup_id"),
                    "campaign_id": value.get("campaign_id"),
                    "created_time": value.get("created_time")
                }
                
                # Create lead in database
                lead = await create_lead_from_facebook(lead_data, db)
                processed_leads.append({
                    "lead_id": str(lead.id),
                    "facebook_leadgen_id": lead_data["leadgen_id"],
                    "status": "processed"
                })
    
    return processed_leads


async def create_lead_from_facebook(
    lead_data: Dict[str, Any],
    db: AsyncSession,
    property_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> Lead:
    """Create a lead from Facebook lead form data.
    
    Args:
        lead_data: Lead data from Facebook
        db: Database session
        property_id: Property/bot ID to associate lead with
        user_id: User ID to associate lead with
        
    Returns:
        Created Lead object
    """
    # Extract field data from lead_data
    field_data = lead_data.get("field_data", [])
    
    # Parse field data into dict
    fields = {}
    for field in field_data:
        name = field.get("name", "").lower()
        values = field.get("values", [])
        if values:
            fields[name] = values[0]
    
    # Extract common fields
    name = fields.get("full_name") or fields.get("name") or "Unknown"
    email = fields.get("email")
    phone = fields.get("phone_number") or fields.get("phone")
    
    # Create lead metadata
    metadata = {
        "facebook_leadgen_id": lead_data.get("leadgen_id"),
        "facebook_page_id": lead_data.get("page_id"),
        "facebook_form_id": lead_data.get("form_id"),
        "facebook_ad_id": lead_data.get("ad_id"),
        "facebook_adgroup_id": lead_data.get("adgroup_id"),
        "facebook_campaign_id": lead_data.get("campaign_id"),
        "facebook_created_time": lead_data.get("created_time"),
        "raw_fields": fields
    }
    
    # Create lead
    lead = Lead(
        name=name,
        email=email,
        phone=phone,
        source=LeadSource.facebook_ads,
        status=LeadStatus.new,
        score=50,  # Default score for Facebook leads
        metadata=metadata,
        property_id=property_id,
        user_id=user_id
    )
    
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    
    return lead


async def fetch_lead_details(
    leadgen_id: str,
    page_access_token: str
) -> Dict[str, Any]:
    """Fetch full lead details from Facebook.
    
    Args:
        leadgen_id: Facebook leadgen ID
        page_access_token: Page access token
        
    Returns:
        Lead details from Facebook
    """
    import httpx
    
    url = f"https://graph.facebook.com/v18.0/{leadgen_id}"
    params = {
        "access_token": page_access_token,
        "fields": "id,ad_id,ad_name,adset_id,adset_name,campaign_id,campaign_name,form_id,field_data,created_time,is_organic"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise IntegrationError(
            message=f"Failed to fetch Facebook lead details: {str(e)}",
            integration_name="facebook_ads",
            details={"leadgen_id": leadgen_id}
        )

"""Facebook Ads campaign management."""

from typing import Dict, Any, Optional, List
from app.integrations.facebook.client import FacebookAdsClient
from app.core.exceptions import IntegrationError


def get_campaigns(client: FacebookAdsClient) -> List[Dict[str, Any]]:
    """
    Get all Facebook campaigns for the connected ad account.
    
    Args:
        client: Facebook Ads client instance
        
    Returns:
        List of campaign dictionaries
    """
    try:
        # Get campaigns from the ad account
        campaigns = client.list_campaigns()
        return campaigns
    except Exception as e:
        raise IntegrationError(
            message=f"Failed to fetch campaigns: {str(e)}",
            integration_name="facebook_ads"
        )


def get_campaign_insights(
    client: FacebookAdsClient,
    campaign_id: str,
    date_preset: str = "last_7d"
) -> Dict[str, Any]:
    """
    Get insights/analytics for a specific campaign.
    
    Args:
        client: Facebook Ads client instance
        campaign_id: Facebook Campaign ID
        date_preset: Time range preset
        
    Returns:
        Campaign insights dictionary
    """
    try:
        insights = client.get_insights(campaign_id, date_preset)
        return insights
    except Exception as e:
        raise IntegrationError(
            message=f"Failed to fetch campaign insights: {str(e)}",
            integration_name="facebook_ads"
        )


async def get_campaign_metrics(
    campaign_id: str,
    date_preset: str = "last_7d"
) -> Dict[str, Any]:
    """Get metrics for a Facebook campaign.
    
    Args:
        campaign_id: Facebook Campaign ID
        date_preset: Time range preset (e.g., 'last_7d', 'last_30d')
        
    Returns:
        Campaign metrics including impressions, clicks, spend, etc.
    """
    client = FacebookAdsClient()
    
    insights = await client.get_campaign_insights(
        campaign_id=campaign_id,
        date_preset=date_preset
    )
    
    # Parse and structure metrics
    metrics = {
        "campaign_id": campaign_id,
        "date_preset": date_preset,
        "impressions": int(insights.get("impressions", 0)),
        "clicks": int(insights.get("clicks", 0)),
        "spend": float(insights.get("spend", 0)),
        "reach": int(insights.get("reach", 0)),
        "cpc": float(insights.get("cpc", 0)),
        "cpm": float(insights.get("cpm", 0)),
        "ctr": float(insights.get("ctr", 0)),
    }
    
    # Extract lead generation actions
    actions = insights.get("actions", [])
    leads = 0
    for action in actions:
        if action.get("action_type") == "lead":
            leads = int(action.get("value", 0))
            break
    
    metrics["leads"] = leads
    
    # Calculate cost per lead
    if leads > 0 and metrics["spend"] > 0:
        metrics["cost_per_lead"] = metrics["spend"] / leads
    else:
        metrics["cost_per_lead"] = 0
    
    return metrics


async def pause_campaign(campaign_id: str) -> Dict[str, Any]:
    """Pause a Facebook campaign.
    
    Args:
        campaign_id: Facebook Campaign ID
        
    Returns:
        Update response
    """
    client = FacebookAdsClient()
    
    return await client.update_campaign(
        campaign_id=campaign_id,
        updates={"status": "PAUSED"}
    )


async def resume_campaign(campaign_id: str) -> Dict[str, Any]:
    """Resume a paused Facebook campaign.
    
    Args:
        campaign_id: Facebook Campaign ID
        
    Returns:
        Update response
    """
    client = FacebookAdsClient()
    
    return await client.update_campaign(
        campaign_id=campaign_id,
        updates={"status": "ACTIVE"}
    )


async def update_budget(
    campaign_id: str,
    daily_budget: Optional[int] = None,
    lifetime_budget: Optional[int] = None
) -> Dict[str, Any]:
    """Update campaign budget.
    
    Args:
        campaign_id: Facebook Campaign ID
        daily_budget: Daily budget in cents (e.g., 5000 for $50/day)
        lifetime_budget: Lifetime budget in cents
        
    Returns:
        Update response
        
    Raises:
        IntegrationError: If neither budget type is provided
    """
    if daily_budget is None and lifetime_budget is None:
        raise IntegrationError(
            message="Must provide either daily_budget or lifetime_budget",
            integration_name="facebook_ads"
        )
    
    client = FacebookAdsClient()
    updates = {}
    
    if daily_budget is not None:
        updates["daily_budget"] = daily_budget
    
    if lifetime_budget is not None:
        updates["lifetime_budget"] = lifetime_budget
    
    return await client.update_campaign(
        campaign_id=campaign_id,
        updates=updates
    )


async def get_campaign_details(
    campaign_id: str,
    include_insights: bool = True
) -> Dict[str, Any]:
    """Get detailed campaign information.
    
    Args:
        campaign_id: Facebook Campaign ID
        include_insights: Whether to include performance insights
        
    Returns:
        Campaign details with optional insights
    """
    client = FacebookAdsClient()
    
    # Get campaign info
    response = await client._request(
        method="GET",
        endpoint=f"/{campaign_id}",
        params={
            "fields": "id,name,status,objective,daily_budget,lifetime_budget,created_time,updated_time"
        }
    )
    
    campaign_data = {
        "id": response.get("id"),
        "name": response.get("name"),
        "status": response.get("status"),
        "objective": response.get("objective"),
        "daily_budget": response.get("daily_budget"),
        "lifetime_budget": response.get("lifetime_budget"),
        "created_time": response.get("created_time"),
        "updated_time": response.get("updated_time")
    }
    
    # Add insights if requested
    if include_insights:
        insights = await get_campaign_metrics(campaign_id)
        campaign_data["insights"] = insights
    
    return campaign_data

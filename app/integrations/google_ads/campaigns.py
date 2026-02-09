"""Google Ads campaign management."""

from typing import Dict, Any, Optional, List
from app.integrations.google_ads.client import GoogleAdsClient
from app.core.exceptions import IntegrationError


async def get_campaign_performance(
    customer_id: str,
    campaign_id: str,
    date_range: str = "LAST_7_DAYS"
) -> Dict[str, Any]:
    """Get detailed performance metrics for a campaign.
    
    Args:
        customer_id: Google Ads Customer ID
        campaign_id: Campaign ID
        date_range: Date range for metrics
        
    Returns:
        Detailed campaign performance data
    """
    client = GoogleAdsClient(customer_id=customer_id)
    
    stats = await client.get_campaign_stats(
        campaign_id=campaign_id,
        date_range=date_range,
        customer_id=customer_id
    )
    
    # Calculate additional metrics
    if stats.get("clicks", 0) > 0 and stats.get("cost", 0) > 0:
        stats["cost_per_click"] = stats["cost"] / stats["clicks"]
    else:
        stats["cost_per_click"] = 0
    
    if stats.get("conversions", 0) > 0 and stats.get("cost", 0) > 0:
        stats["cost_per_conversion"] = stats["cost"] / stats["conversions"]
    else:
        stats["cost_per_conversion"] = 0
    
    if stats.get("conversions", 0) > 0 and stats.get("clicks", 0) > 0:
        stats["conversion_rate"] = (stats["conversions"] / stats["clicks"]) * 100
    else:
        stats["conversion_rate"] = 0
    
    return stats


async def update_campaign_status(
    customer_id: str,
    campaign_id: str,
    status: str
) -> Dict[str, Any]:
    """Update campaign status (ENABLED, PAUSED, REMOVED).
    
    Args:
        customer_id: Google Ads Customer ID
        campaign_id: Campaign ID
        status: New status ('ENABLED', 'PAUSED', 'REMOVED')
        
    Returns:
        Update response
        
    Raises:
        IntegrationError: If status is invalid
    """
    valid_statuses = ["ENABLED", "PAUSED", "REMOVED"]
    if status not in valid_statuses:
        raise IntegrationError(
            message=f"Invalid campaign status: {status}",
            integration_name="google_ads",
            details={"valid_statuses": valid_statuses}
        )
    
    client = GoogleAdsClient(customer_id=customer_id)
    
    # Use GoogleAdsFieldService to update campaign
    mutation = {
        "operations": [
            {
                "update": {
                    "resourceName": f"customers/{customer_id}/campaigns/{campaign_id}",
                    "status": status
                },
                "updateMask": "status"
            }
        ]
    }
    
    return await client._request(
        method="POST",
        endpoint=f"/customers/{customer_id}/campaigns:mutate",
        data=mutation
    )


async def pause_campaign(customer_id: str, campaign_id: str) -> Dict[str, Any]:
    """Pause a Google Ads campaign.
    
    Args:
        customer_id: Google Ads Customer ID
        campaign_id: Campaign ID
        
    Returns:
        Update response
    """
    return await update_campaign_status(customer_id, campaign_id, "PAUSED")


async def enable_campaign(customer_id: str, campaign_id: str) -> Dict[str, Any]:
    """Enable a paused Google Ads campaign.
    
    Args:
        customer_id: Google Ads Customer ID
        campaign_id: Campaign ID
        
    Returns:
        Update response
    """
    return await update_campaign_status(customer_id, campaign_id, "ENABLED")


async def get_all_campaigns_performance(
    customer_id: str,
    date_range: str = "LAST_7_DAYS"
) -> List[Dict[str, Any]]:
    """Get performance data for all campaigns.
    
    Args:
        customer_id: Google Ads Customer ID
        date_range: Date range for metrics
        
    Returns:
        List of campaign performance data
    """
    client = GoogleAdsClient(customer_id=customer_id)
    
    campaigns = await client.get_campaigns(customer_id=customer_id)
    
    performance_data = []
    for campaign in campaigns:
        try:
            stats = await get_campaign_performance(
                customer_id=customer_id,
                campaign_id=campaign["id"],
                date_range=date_range
            )
            performance_data.append(stats)
        except Exception as e:
            # Log error but continue with other campaigns
            print(f"Error fetching performance for campaign {campaign['id']}: {str(e)}")
    
    return performance_data

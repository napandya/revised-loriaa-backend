"""Facebook Ads API client."""

from typing import Optional, Dict, Any, List
from uuid import UUID
import httpx
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.exceptions import IntegrationError


class FacebookAdsClient:
    """Client for interacting with Facebook Ads API."""
    
    def __init__(self, db: Session = None, user_id: UUID = None):
        """Initialize Facebook Ads client with settings."""
        self.db = db
        self.user_id = user_id
        self.app_id = settings.FACEBOOK_APP_ID
        self.app_secret = settings.FACEBOOK_APP_SECRET
        self.access_token = settings.FACEBOOK_ACCESS_TOKEN
        self.ad_account_id = getattr(settings, 'FACEBOOK_AD_ACCOUNT_ID', None)
        self.base_url = "https://graph.facebook.com/v18.0"
        
        if not self.access_token:
            raise IntegrationError(
                message="Facebook access token not configured",
                integration_name="facebook_ads"
            )
    
    def list_campaigns(self) -> List[Dict[str, Any]]:
        """
        Synchronous method to list campaigns.
        
        Returns:
            List of campaign dictionaries
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        account_id = self.ad_account_id or "act_placeholder"
        return loop.run_until_complete(self.get_campaigns(account_id))
    
    def get_insights(self, campaign_id: str, date_preset: str = "last_7d") -> Dict[str, Any]:
        """
        Synchronous method to get campaign insights.
        
        Args:
            campaign_id: Campaign ID
            date_preset: Time range
            
        Returns:
            Insights dictionary
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.get_campaign_insights(campaign_id, date_preset))
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to Facebook Ads API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters
            
        Returns:
            Response data as dictionary
            
        Raises:
            IntegrationError: If the request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        # Add access token to all requests
        if params is None:
            params = {}
        params["access_token"] = self.access_token
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    timeout=30.0
                )
                
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else str(e)
            raise IntegrationError(
                message=f"Facebook Ads API request failed: {e.response.status_code}",
                integration_name="facebook_ads",
                details={
                    "status_code": e.response.status_code,
                    "error": error_detail,
                    "endpoint": endpoint
                }
            )
        except httpx.RequestError as e:
            raise IntegrationError(
                message=f"Facebook Ads API connection error: {str(e)}",
                integration_name="facebook_ads",
                details={"endpoint": endpoint}
            )
        except Exception as e:
            raise IntegrationError(
                message=f"Unexpected error during Facebook Ads API request: {str(e)}",
                integration_name="facebook_ads",
                details={"endpoint": endpoint}
            )
    
    async def get_campaigns(
        self,
        account_id: str,
        fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get all campaigns for an ad account.
        
        Args:
            account_id: Facebook Ad Account ID (e.g., 'act_123456789')
            fields: List of fields to retrieve
            
        Returns:
            List of campaign data dictionaries
        """
        if fields is None:
            fields = ["id", "name", "status", "objective", "daily_budget", "lifetime_budget"]
        
        params = {"fields": ",".join(fields)}
        response = await self._request(
            method="GET",
            endpoint=f"/{account_id}/campaigns",
            params=params
        )
        
        return response.get("data", [])
    
    async def get_campaign_insights(
        self,
        campaign_id: str,
        date_preset: str = "last_7d",
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get insights/metrics for a campaign.
        
        Args:
            campaign_id: Facebook Campaign ID
            date_preset: Time range preset (e.g., 'last_7d', 'last_30d')
            fields: List of metric fields to retrieve
            
        Returns:
            Campaign insights data
        """
        if fields is None:
            fields = [
                "impressions",
                "clicks",
                "spend",
                "reach",
                "actions",
                "cost_per_action_type",
                "cpc",
                "cpm",
                "ctr"
            ]
        
        params = {
            "date_preset": date_preset,
            "fields": ",".join(fields)
        }
        
        response = await self._request(
            method="GET",
            endpoint=f"/{campaign_id}/insights",
            params=params
        )
        
        data = response.get("data", [])
        return data[0] if data else {}
    
    async def create_campaign(
        self,
        account_id: str,
        name: str,
        objective: str,
        status: str = "PAUSED",
        special_ad_categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new campaign.
        
        Args:
            account_id: Facebook Ad Account ID
            name: Campaign name
            objective: Campaign objective (e.g., 'LEAD_GENERATION', 'CONVERSIONS')
            status: Campaign status ('ACTIVE', 'PAUSED')
            special_ad_categories: List of special ad categories
            
        Returns:
            Created campaign data
        """
        data = {
            "name": name,
            "objective": objective,
            "status": status
        }
        
        if special_ad_categories:
            data["special_ad_categories"] = special_ad_categories
        
        return await self._request(
            method="POST",
            endpoint=f"/{account_id}/campaigns",
            data=data
        )
    
    async def update_campaign(
        self,
        campaign_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing campaign.
        
        Args:
            campaign_id: Facebook Campaign ID
            updates: Dictionary of fields to update
            
        Returns:
            Update response data
        """
        return await self._request(
            method="POST",
            endpoint=f"/{campaign_id}",
            data=updates
        )

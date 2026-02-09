"""Google Ads API client."""

from typing import Optional, Dict, Any, List
import httpx
from app.core.config import settings
from app.core.exceptions import IntegrationError


class GoogleAdsClient:
    """Client for interacting with Google Ads API."""
    
    def __init__(self, customer_id: Optional[str] = None):
        """Initialize Google Ads client with settings.
        
        Args:
            customer_id: Google Ads Customer ID (without hyphens)
        """
        self.developer_token = settings.GOOGLE_ADS_DEVELOPER_TOKEN
        self.client_id = settings.GOOGLE_ADS_CLIENT_ID
        self.client_secret = settings.GOOGLE_ADS_CLIENT_SECRET
        self.refresh_token = settings.GOOGLE_ADS_REFRESH_TOKEN
        self.customer_id = customer_id or settings.GOOGLE_ADS_CUSTOMER_ID
        self.base_url = "https://googleads.googleapis.com/v15"
        
        if not self.developer_token:
            raise IntegrationError(
                message="Google Ads developer token not configured",
                integration_name="google_ads"
            )
        
        if not self.customer_id:
            raise IntegrationError(
                message="Google Ads customer ID not configured",
                integration_name="google_ads"
            )
        
        self._access_token: Optional[str] = None
    
    async def _get_access_token(self) -> str:
        """Get or refresh OAuth2 access token.
        
        Returns:
            Valid access token
            
        Raises:
            IntegrationError: If token refresh fails
        """
        if self._access_token:
            return self._access_token
        
        token_url = "https://oauth2.googleapis.com/token"
        
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=data, timeout=30.0)
                response.raise_for_status()
                token_data = response.json()
                self._access_token = token_data["access_token"]
                return self._access_token
        except Exception as e:
            raise IntegrationError(
                message=f"Failed to refresh Google Ads access token: {str(e)}",
                integration_name="google_ads"
            )
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to Google Ads API.
        
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
        access_token = await self._get_access_token()
        url = f"{self.base_url}{endpoint}"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "developer-token": self.developer_token,
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    params=params,
                    timeout=30.0
                )
                
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else str(e)
            raise IntegrationError(
                message=f"Google Ads API request failed: {e.response.status_code}",
                integration_name="google_ads",
                details={
                    "status_code": e.response.status_code,
                    "error": error_detail,
                    "endpoint": endpoint
                }
            )
        except httpx.RequestError as e:
            raise IntegrationError(
                message=f"Google Ads API connection error: {str(e)}",
                integration_name="google_ads",
                details={"endpoint": endpoint}
            )
        except Exception as e:
            raise IntegrationError(
                message=f"Unexpected error during Google Ads API request: {str(e)}",
                integration_name="google_ads",
                details={"endpoint": endpoint}
            )
    
    async def search(
        self,
        query: str,
        customer_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Execute a Google Ads Query Language (GAQL) search.
        
        Args:
            query: GAQL query string
            customer_id: Optional customer ID to override default
            
        Returns:
            List of result rows
        """
        cid = customer_id or self.customer_id
        
        response = await self._request(
            method="POST",
            endpoint=f"/customers/{cid}/googleAds:search",
            data={"query": query}
        )
        
        return response.get("results", [])
    
    async def get_campaigns(
        self,
        customer_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all campaigns for a customer.
        
        Args:
            customer_id: Optional customer ID to override default
            
        Returns:
            List of campaign data
        """
        query = """
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                campaign.advertising_channel_type,
                campaign.start_date,
                campaign.end_date
            FROM campaign
            WHERE campaign.status != 'REMOVED'
            ORDER BY campaign.name
        """
        
        results = await self.search(query, customer_id)
        
        campaigns = []
        for row in results:
            campaign = row.get("campaign", {})
            campaigns.append({
                "id": campaign.get("id"),
                "name": campaign.get("name"),
                "status": campaign.get("status"),
                "channel_type": campaign.get("advertisingChannelType"),
                "start_date": campaign.get("startDate"),
                "end_date": campaign.get("endDate")
            })
        
        return campaigns
    
    async def get_campaign_stats(
        self,
        campaign_id: str,
        date_range: str = "LAST_7_DAYS",
        customer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get performance statistics for a campaign.
        
        Args:
            campaign_id: Campaign ID
            date_range: Date range (e.g., 'LAST_7_DAYS', 'LAST_30_DAYS')
            customer_id: Optional customer ID to override default
            
        Returns:
            Campaign statistics
        """
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value,
                metrics.average_cpc,
                metrics.average_cpm,
                metrics.ctr
            FROM campaign
            WHERE campaign.id = {campaign_id}
            AND segments.date DURING {date_range}
        """
        
        results = await self.search(query, customer_id)
        
        if not results:
            return {}
        
        row = results[0]
        campaign = row.get("campaign", {})
        metrics = row.get("metrics", {})
        
        return {
            "campaign_id": campaign.get("id"),
            "campaign_name": campaign.get("name"),
            "impressions": int(metrics.get("impressions", 0)),
            "clicks": int(metrics.get("clicks", 0)),
            "cost": float(metrics.get("costMicros", 0)) / 1_000_000,
            "conversions": float(metrics.get("conversions", 0)),
            "conversions_value": float(metrics.get("conversionsValue", 0)),
            "avg_cpc": float(metrics.get("averageCpc", 0)) / 1_000_000,
            "avg_cpm": float(metrics.get("averageCpm", 0)) / 1_000_000,
            "ctr": float(metrics.get("ctr", 0))
        }

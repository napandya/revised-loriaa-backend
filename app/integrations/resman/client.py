"""ResMan PMS API client."""

from typing import Optional, Dict, Any, List
import httpx
from app.core.config import settings
from app.core.exceptions import IntegrationError, RateLimitError


class ResManClient:
    """Client for interacting with ResMan Property Management System API."""
    
    def __init__(self):
        """Initialize ResMan client with settings."""
        self.api_key = settings.RESMAN_API_KEY
        self.integration_partner_id = settings.RESMAN_INTEGRATION_PARTNER_ID
        self.base_url = settings.RESMAN_BASE_URL
        
        if not self.api_key:
            raise IntegrationError(
                message="ResMan API key not configured",
                integration_name="resman"
            )
        
        if not self.integration_partner_id:
            raise IntegrationError(
                message="ResMan integration partner ID not configured",
                integration_name="resman"
            )
        
        self.headers = {
            "X-APIKey": self.api_key,
            "IntegrationPartnerID": self.integration_partner_id,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to ResMan API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters
            
        Returns:
            Response data as dictionary
            
        Raises:
            IntegrationError: If the request fails
            RateLimitError: If rate limit is exceeded
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data,
                    params=params,
                    timeout=30.0
                )
                
                # Check for rate limiting
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    raise RateLimitError(
                        message="ResMan API rate limit exceeded",
                        retry_after=int(retry_after) if retry_after else None
                    )
                
                response.raise_for_status()
                return response.json()
                
        except RateLimitError:
            raise
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else str(e)
            raise IntegrationError(
                message=f"ResMan API request failed: {e.response.status_code}",
                integration_name="resman",
                details={
                    "status_code": e.response.status_code,
                    "error": error_detail,
                    "endpoint": endpoint
                }
            )
        except httpx.RequestError as e:
            raise IntegrationError(
                message=f"ResMan API connection error: {str(e)}",
                integration_name="resman",
                details={"endpoint": endpoint}
            )
        except Exception as e:
            raise IntegrationError(
                message=f"Unexpected error during ResMan API request: {str(e)}",
                integration_name="resman",
                details={"endpoint": endpoint}
            )
    
    async def get_properties(
        self,
        include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """Get all properties from ResMan.
        
        Args:
            include_inactive: Whether to include inactive properties
            
        Returns:
            List of property data
        """
        params = {}
        if not include_inactive:
            params["status"] = "Active"
        
        response = await self._request(
            method="GET",
            endpoint="/properties",
            params=params
        )
        
        return response.get("Properties", [])
    
    async def get_property(self, property_id: str) -> Dict[str, Any]:
        """Get details for a specific property.
        
        Args:
            property_id: ResMan property ID
            
        Returns:
            Property details
        """
        return await self._request(
            method="GET",
            endpoint=f"/properties/{property_id}"
        )
    
    async def get_units(
        self,
        property_id: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get units for a property.
        
        Args:
            property_id: ResMan property ID
            status: Filter by unit status (e.g., 'Available', 'Occupied')
            
        Returns:
            List of unit data
        """
        params = {}
        if status:
            params["status"] = status
        
        response = await self._request(
            method="GET",
            endpoint=f"/properties/{property_id}/units",
            params=params
        )
        
        return response.get("Units", [])
    
    async def get_unit(
        self,
        property_id: str,
        unit_id: str
    ) -> Dict[str, Any]:
        """Get details for a specific unit.
        
        Args:
            property_id: ResMan property ID
            unit_id: ResMan unit ID
            
        Returns:
            Unit details
        """
        return await self._request(
            method="GET",
            endpoint=f"/properties/{property_id}/units/{unit_id}"
        )
    
    async def get_residents(
        self,
        property_id: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get residents for a property.
        
        Args:
            property_id: ResMan property ID
            status: Filter by resident status (e.g., 'Current', 'Past', 'Future')
            
        Returns:
            List of resident data
        """
        params = {}
        if status:
            params["status"] = status
        
        response = await self._request(
            method="GET",
            endpoint=f"/properties/{property_id}/residents",
            params=params
        )
        
        return response.get("Residents", [])
    
    async def get_resident(
        self,
        property_id: str,
        resident_id: str
    ) -> Dict[str, Any]:
        """Get details for a specific resident.
        
        Args:
            property_id: ResMan property ID
            resident_id: ResMan resident ID
            
        Returns:
            Resident details
        """
        return await self._request(
            method="GET",
            endpoint=f"/properties/{property_id}/residents/{resident_id}"
        )
    
    async def search_units(
        self,
        property_id: str,
        bedrooms: Optional[int] = None,
        bathrooms: Optional[float] = None,
        min_sqft: Optional[int] = None,
        max_sqft: Optional[int] = None,
        available_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for available units with filters.
        
        Args:
            property_id: ResMan property ID
            bedrooms: Number of bedrooms
            bathrooms: Number of bathrooms
            min_sqft: Minimum square footage
            max_sqft: Maximum square footage
            available_date: Available date (YYYY-MM-DD)
            
        Returns:
            List of matching units
        """
        params = {"status": "Available"}
        
        if bedrooms is not None:
            params["bedrooms"] = bedrooms
        if bathrooms is not None:
            params["bathrooms"] = bathrooms
        if min_sqft is not None:
            params["minSqft"] = min_sqft
        if max_sqft is not None:
            params["maxSqft"] = max_sqft
        if available_date:
            params["availableDate"] = available_date
        
        response = await self._request(
            method="GET",
            endpoint=f"/properties/{property_id}/units/search",
            params=params
        )
        
        return response.get("Units", [])

"""Google Ads conversion tracking."""

from typing import Dict, Any, Optional, List
from datetime import datetime
from app.integrations.google_ads.client import GoogleAdsClient
from app.core.exceptions import IntegrationError


async def track_conversion(
    customer_id: str,
    conversion_action: str,
    gclid: str,
    conversion_value: Optional[float] = None,
    conversion_time: Optional[datetime] = None,
    order_id: Optional[str] = None
) -> Dict[str, Any]:
    """Track an offline conversion in Google Ads.
    
    Args:
        customer_id: Google Ads Customer ID
        conversion_action: Conversion action resource name
        gclid: Google Click ID from the ad click
        conversion_value: Conversion value (e.g., revenue)
        conversion_time: Time of conversion (defaults to now)
        order_id: Optional order/transaction ID
        
    Returns:
        Conversion upload response
    """
    client = GoogleAdsClient(customer_id=customer_id)
    
    if conversion_time is None:
        conversion_time = datetime.utcnow()
    
    # Format conversion time as required by API
    conversion_datetime = conversion_time.strftime("%Y-%m-%d %H:%M:%S+00:00")
    
    conversion_data = {
        "gclid": gclid,
        "conversionAction": conversion_action,
        "conversionDateTime": conversion_datetime
    }
    
    if conversion_value is not None:
        conversion_data["conversionValue"] = conversion_value
    
    if order_id:
        conversion_data["orderId"] = order_id
    
    payload = {
        "conversions": [conversion_data],
        "partialFailure": True
    }
    
    return await client._request(
        method="POST",
        endpoint=f"/customers/{customer_id}:uploadClickConversions",
        data=payload
    )


async def track_call_conversion(
    customer_id: str,
    conversion_action: str,
    caller_id: str,
    call_start_time: datetime,
    conversion_value: Optional[float] = None
) -> Dict[str, Any]:
    """Track a call conversion in Google Ads.
    
    Args:
        customer_id: Google Ads Customer ID
        conversion_action: Conversion action resource name
        caller_id: Caller phone number
        call_start_time: Time when call started
        conversion_value: Conversion value
        
    Returns:
        Conversion upload response
    """
    client = GoogleAdsClient(customer_id=customer_id)
    
    call_datetime = call_start_time.strftime("%Y-%m-%d %H:%M:%S+00:00")
    
    conversion_data = {
        "callerId": caller_id,
        "callStartDateTime": call_datetime,
        "conversionAction": conversion_action,
        "conversionDateTime": call_datetime
    }
    
    if conversion_value is not None:
        conversion_data["conversionValue"] = conversion_value
    
    payload = {
        "conversions": [conversion_data],
        "partialFailure": True
    }
    
    return await client._request(
        method="POST",
        endpoint=f"/customers/{customer_id}:uploadCallConversions",
        data=payload
    )


async def get_conversion_actions(
    customer_id: str,
    status: str = "ENABLED"
) -> List[Dict[str, Any]]:
    """Get all conversion actions for a customer.
    
    Args:
        customer_id: Google Ads Customer ID
        status: Filter by status ('ENABLED', 'REMOVED')
        
    Returns:
        List of conversion actions
    """
    client = GoogleAdsClient(customer_id=customer_id)
    
    query = f"""
        SELECT
            conversion_action.id,
            conversion_action.name,
            conversion_action.type,
            conversion_action.status,
            conversion_action.category
        FROM conversion_action
        WHERE conversion_action.status = '{status}'
    """
    
    results = await client.search(query, customer_id)
    
    actions = []
    for row in results:
        action = row.get("conversionAction", {})
        actions.append({
            "id": action.get("id"),
            "name": action.get("name"),
            "type": action.get("type"),
            "status": action.get("status"),
            "category": action.get("category"),
            "resource_name": action.get("resourceName")
        })
    
    return actions


async def track_lead_conversion(
    customer_id: str,
    gclid: str,
    lead_value: Optional[float] = None
) -> Dict[str, Any]:
    """Track a lead generation conversion.
    
    Args:
        customer_id: Google Ads Customer ID
        gclid: Google Click ID
        lead_value: Estimated lead value
        
    Returns:
        Conversion tracking response
    """
    # Get the lead conversion action
    actions = await get_conversion_actions(customer_id)
    
    # Find lead conversion action
    lead_action = None
    for action in actions:
        if action.get("category") == "LEAD" or "lead" in action.get("name", "").lower():
            lead_action = action
            break
    
    if not lead_action:
        raise IntegrationError(
            message="No lead conversion action found",
            integration_name="google_ads",
            details={"customer_id": customer_id}
        )
    
    return await track_conversion(
        customer_id=customer_id,
        conversion_action=lead_action["resource_name"],
        gclid=gclid,
        conversion_value=lead_value
    )

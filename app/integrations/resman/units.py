"""ResMan unit availability management."""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
from app.integrations.resman.client import ResManClient
from app.core.exceptions import IntegrationError


async def get_available_units(
    property_id: str,
    bedrooms: Optional[int] = None,
    move_in_date: Optional[str] = None,
    max_rent: Optional[float] = None
) -> List[Dict[str, Any]]:
    """Get available units for a property with optional filters.
    
    Args:
        property_id: ResMan property ID
        bedrooms: Filter by number of bedrooms
        move_in_date: Filter by move-in date (YYYY-MM-DD)
        max_rent: Maximum monthly rent
        
    Returns:
        List of available units with pricing
    """
    client = ResManClient()
    
    # Search for available units
    units = await client.search_units(
        property_id=property_id,
        bedrooms=bedrooms,
        available_date=move_in_date
    )
    
    # Filter by rent if specified
    if max_rent:
        units = [u for u in units if u.get("Rent", float('inf')) <= max_rent]
    
    # Format unit data
    available = []
    for unit in units:
        available.append({
            "unit_id": unit.get("UnitID"),
            "unit_number": unit.get("UnitNumber"),
            "bedrooms": unit.get("Bedrooms"),
            "bathrooms": unit.get("Bathrooms"),
            "sqft": unit.get("SquareFeet"),
            "rent": unit.get("Rent"),
            "deposit": unit.get("Deposit"),
            "available_date": unit.get("AvailableDate"),
            "floor_plan": unit.get("FloorPlan"),
            "features": unit.get("Features", [])
        })
    
    return available


async def get_unit_pricing(
    property_id: str,
    unit_id: str
) -> Dict[str, Any]:
    """Get pricing information for a specific unit.
    
    Args:
        property_id: ResMan property ID
        unit_id: ResMan unit ID
        
    Returns:
        Unit pricing details
    """
    client = ResManClient()
    
    unit = await client.get_unit(property_id, unit_id)
    
    pricing = {
        "unit_id": unit_id,
        "unit_number": unit.get("UnitNumber"),
        "rent": unit.get("Rent"),
        "deposit": unit.get("Deposit"),
        "fees": [],
        "total_move_in_cost": 0
    }
    
    # Extract fees
    fees = unit.get("Fees", [])
    for fee in fees:
        pricing["fees"].append({
            "name": fee.get("Name"),
            "amount": fee.get("Amount"),
            "type": fee.get("Type")  # One-time or Recurring
        })
    
    # Calculate total move-in cost
    rent = float(unit.get("Rent", 0))
    deposit = float(unit.get("Deposit", 0))
    one_time_fees = sum(
        float(f.get("Amount", 0)) 
        for f in fees 
        if f.get("Type") == "OneTime"
    )
    
    pricing["total_move_in_cost"] = rent + deposit + one_time_fees
    
    return pricing


async def check_unit_status(
    property_id: str,
    unit_id: str
) -> Dict[str, Any]:
    """Check the current status of a unit.
    
    Args:
        property_id: ResMan property ID
        unit_id: ResMan unit ID
        
    Returns:
        Unit status information
    """
    client = ResManClient()
    
    unit = await client.get_unit(property_id, unit_id)
    
    return {
        "unit_id": unit_id,
        "unit_number": unit.get("UnitNumber"),
        "status": unit.get("Status"),  # Available, Occupied, Notice, etc.
        "available_date": unit.get("AvailableDate"),
        "occupied": unit.get("Status") == "Occupied",
        "reserved": unit.get("Status") == "Reserved",
        "lease_end_date": unit.get("LeaseEndDate")
    }


async def get_unit_details(
    property_id: str,
    unit_id: str,
    include_pricing: bool = True
) -> Dict[str, Any]:
    """Get comprehensive unit details.
    
    Args:
        property_id: ResMan property ID
        unit_id: ResMan unit ID
        include_pricing: Whether to include pricing information
        
    Returns:
        Complete unit information
    """
    client = ResManClient()
    
    unit = await client.get_unit(property_id, unit_id)
    
    details = {
        "unit_id": unit.get("UnitID"),
        "unit_number": unit.get("UnitNumber"),
        "building": unit.get("Building"),
        "floor": unit.get("Floor"),
        "status": unit.get("Status"),
        "bedrooms": unit.get("Bedrooms"),
        "bathrooms": unit.get("Bathrooms"),
        "sqft": unit.get("SquareFeet"),
        "floor_plan": unit.get("FloorPlan"),
        "available_date": unit.get("AvailableDate"),
        "features": unit.get("Features", []),
        "amenities": unit.get("Amenities", []),
        "description": unit.get("Description")
    }
    
    if include_pricing:
        pricing = await get_unit_pricing(property_id, unit_id)
        details["pricing"] = pricing
    
    return details


async def get_units_by_floorplan(
    property_id: str,
    floor_plan_name: str,
    available_only: bool = True
) -> List[Dict[str, Any]]:
    """Get all units for a specific floor plan.
    
    Args:
        property_id: ResMan property ID
        floor_plan_name: Floor plan name
        available_only: Only return available units
        
    Returns:
        List of units matching the floor plan
    """
    client = ResManClient()
    
    # Get all units
    status = "Available" if available_only else None
    units = await client.get_units(property_id, status=status)
    
    # Filter by floor plan
    matching_units = [
        {
            "unit_id": u.get("UnitID"),
            "unit_number": u.get("UnitNumber"),
            "status": u.get("Status"),
            "rent": u.get("Rent"),
            "available_date": u.get("AvailableDate")
        }
        for u in units
        if u.get("FloorPlan") == floor_plan_name
    ]
    
    return matching_units


async def search_units_by_criteria(
    property_id: str,
    criteria: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Search units by multiple criteria.
    
    Args:
        property_id: ResMan property ID
        criteria: Search criteria dictionary
            - bedrooms: int
            - bathrooms: float
            - min_sqft: int
            - max_sqft: int
            - max_rent: float
            - move_in_date: str (YYYY-MM-DD)
            
    Returns:
        List of matching units
    """
    client = ResManClient()
    
    # Extract criteria
    bedrooms = criteria.get("bedrooms")
    bathrooms = criteria.get("bathrooms")
    min_sqft = criteria.get("min_sqft")
    max_sqft = criteria.get("max_sqft")
    max_rent = criteria.get("max_rent")
    move_in_date = criteria.get("move_in_date")
    
    # Search with ResMan API
    units = await client.search_units(
        property_id=property_id,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        min_sqft=min_sqft,
        max_sqft=max_sqft,
        available_date=move_in_date
    )
    
    # Apply additional filters
    if max_rent:
        units = [u for u in units if u.get("Rent", float('inf')) <= max_rent]
    
    # Format results
    results = []
    for unit in units:
        results.append({
            "unit_id": unit.get("UnitID"),
            "unit_number": unit.get("UnitNumber"),
            "bedrooms": unit.get("Bedrooms"),
            "bathrooms": unit.get("Bathrooms"),
            "sqft": unit.get("SquareFeet"),
            "rent": unit.get("Rent"),
            "available_date": unit.get("AvailableDate"),
            "floor_plan": unit.get("FloorPlan")
        })
    
    return results

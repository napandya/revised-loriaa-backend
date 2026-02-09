"""ResMan resident data management."""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.integrations.resman.client import ResManClient
from app.core.exceptions import IntegrationError


async def get_residents(
    property_id: str,
    status: Optional[str] = "Current"
) -> List[Dict[str, Any]]:
    """Get residents for a property.
    
    Args:
        property_id: ResMan property ID
        status: Resident status filter ('Current', 'Past', 'Future')
        
    Returns:
        List of resident data
    """
    client = ResManClient()
    
    residents = await client.get_residents(property_id, status=status)
    
    # Format resident data
    formatted = []
    for resident in residents:
        formatted.append({
            "resident_id": resident.get("ResidentID"),
            "name": f"{resident.get('FirstName', '')} {resident.get('LastName', '')}",
            "unit_number": resident.get("UnitNumber"),
            "lease_start": resident.get("LeaseStartDate"),
            "lease_end": resident.get("LeaseEndDate"),
            "status": resident.get("Status"),
            "phone": resident.get("Phone"),
            "email": resident.get("Email")
        })
    
    return formatted


async def get_resident_details(
    property_id: str,
    resident_id: str
) -> Dict[str, Any]:
    """Get detailed information for a specific resident.
    
    Args:
        property_id: ResMan property ID
        resident_id: ResMan resident ID
        
    Returns:
        Resident details
    """
    client = ResManClient()
    
    resident = await client.get_resident(property_id, resident_id)
    
    details = {
        "resident_id": resident.get("ResidentID"),
        "personal_info": {
            "first_name": resident.get("FirstName"),
            "last_name": resident.get("LastName"),
            "date_of_birth": resident.get("DateOfBirth"),
            "ssn_last_4": resident.get("SSNLast4")
        },
        "contact": {
            "phone": resident.get("Phone"),
            "mobile": resident.get("Mobile"),
            "email": resident.get("Email"),
            "emergency_contact": resident.get("EmergencyContact")
        },
        "lease_info": {
            "unit_id": resident.get("UnitID"),
            "unit_number": resident.get("UnitNumber"),
            "lease_start": resident.get("LeaseStartDate"),
            "lease_end": resident.get("LeaseEndDate"),
            "lease_term": resident.get("LeaseTerm"),
            "rent": resident.get("Rent"),
            "status": resident.get("Status")
        },
        "occupants": resident.get("Occupants", []),
        "pets": resident.get("Pets", []),
        "vehicles": resident.get("Vehicles", [])
    }
    
    return details


async def get_current_residents_count(property_id: str) -> int:
    """Get count of current residents for a property.
    
    Args:
        property_id: ResMan property ID
        
    Returns:
        Number of current residents
    """
    residents = await get_residents(property_id, status="Current")
    return len(residents)


async def search_resident_by_name(
    property_id: str,
    name: str
) -> List[Dict[str, Any]]:
    """Search for residents by name.
    
    Args:
        property_id: ResMan property ID
        name: Name to search for (first, last, or full name)
        
    Returns:
        List of matching residents
    """
    # Get all residents
    all_residents = await get_residents(property_id, status=None)
    
    # Search by name (case-insensitive)
    name_lower = name.lower()
    matches = [
        r for r in all_residents
        if name_lower in r.get("name", "").lower()
    ]
    
    return matches


async def search_resident_by_unit(
    property_id: str,
    unit_number: str
) -> Optional[Dict[str, Any]]:
    """Find resident(s) in a specific unit.
    
    Args:
        property_id: ResMan property ID
        unit_number: Unit number
        
    Returns:
        Resident data if found, None otherwise
    """
    residents = await get_residents(property_id, status="Current")
    
    for resident in residents:
        if resident.get("unit_number") == unit_number:
            # Get full details
            return await get_resident_details(
                property_id,
                resident["resident_id"]
            )
    
    return None


async def get_residents_with_expiring_leases(
    property_id: str,
    days: int = 60
) -> List[Dict[str, Any]]:
    """Get residents with leases expiring within a specified number of days.
    
    Args:
        property_id: ResMan property ID
        days: Number of days to look ahead
        
    Returns:
        List of residents with expiring leases
    """
    from datetime import timedelta
    
    residents = await get_residents(property_id, status="Current")
    
    # Calculate cutoff date
    today = datetime.now().date()
    cutoff_date = today + timedelta(days=days)
    
    expiring = []
    for resident in residents:
        lease_end_str = resident.get("lease_end")
        if lease_end_str:
            try:
                lease_end = datetime.strptime(lease_end_str, "%Y-%m-%d").date()
                if today <= lease_end <= cutoff_date:
                    resident["days_until_expiration"] = (lease_end - today).days
                    expiring.append(resident)
            except ValueError:
                continue
    
    # Sort by expiration date
    expiring.sort(key=lambda r: r.get("lease_end", ""))
    
    return expiring


async def get_resident_balance(
    property_id: str,
    resident_id: str
) -> Dict[str, Any]:
    """Get account balance for a resident.
    
    Note: This is a placeholder as ResMan balance API endpoints
    may vary by configuration. Implement based on actual API.
    
    Args:
        property_id: ResMan property ID
        resident_id: ResMan resident ID
        
    Returns:
        Balance information
    """
    client = ResManClient()
    
    # This is a placeholder - actual endpoint may differ
    try:
        balance_data = await client._request(
            method="GET",
            endpoint=f"/properties/{property_id}/residents/{resident_id}/balance"
        )
        
        return {
            "resident_id": resident_id,
            "current_balance": balance_data.get("CurrentBalance", 0),
            "charges": balance_data.get("Charges", []),
            "payments": balance_data.get("Payments", []),
            "last_payment_date": balance_data.get("LastPaymentDate")
        }
    except Exception as e:
        # Return empty balance if endpoint not available
        return {
            "resident_id": resident_id,
            "current_balance": 0,
            "charges": [],
            "payments": [],
            "error": "Balance data not available"
        }


async def get_move_ins_this_month(property_id: str) -> List[Dict[str, Any]]:
    """Get residents moving in this month.
    
    Args:
        property_id: ResMan property ID
        
    Returns:
        List of upcoming move-ins
    """
    residents = await get_residents(property_id, status="Future")
    
    today = datetime.now().date()
    this_month = today.replace(day=1)
    next_month = (this_month + timedelta(days=32)).replace(day=1)
    
    move_ins = []
    for resident in residents:
        lease_start_str = resident.get("lease_start")
        if lease_start_str:
            try:
                lease_start = datetime.strptime(lease_start_str, "%Y-%m-%d").date()
                if this_month <= lease_start < next_month:
                    move_ins.append(resident)
            except ValueError:
                continue
    
    return move_ins

"""ResMan property synchronization."""

from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.integrations.resman.client import ResManClient
from app.core.exceptions import IntegrationError


async def sync_properties(
    db: AsyncSession,
    include_inactive: bool = False
) -> Dict[str, Any]:
    """Sync all properties from ResMan to local database.
    
    Args:
        db: Database session
        include_inactive: Whether to sync inactive properties
        
    Returns:
        Sync summary with counts
    """
    client = ResManClient()
    
    # Fetch properties from ResMan
    properties = await client.get_properties(include_inactive=include_inactive)
    
    summary = {
        "total": len(properties),
        "created": 0,
        "updated": 0,
        "errors": 0,
        "properties": []
    }
    
    for prop_data in properties:
        try:
            result = await sync_property(db, prop_data)
            
            if result["action"] == "created":
                summary["created"] += 1
            else:
                summary["updated"] += 1
            
            summary["properties"].append({
                "id": result["property_id"],
                "name": result["name"],
                "action": result["action"]
            })
        except Exception as e:
            summary["errors"] += 1
            print(f"Error syncing property {prop_data.get('PropertyID')}: {str(e)}")
    
    return summary


async def sync_property(
    db: AsyncSession,
    property_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Sync a single property to local database.
    
    Args:
        db: Database session
        property_data: Property data from ResMan
        
    Returns:
        Sync result
    """
    from app.models.bot import Bot
    
    property_id = property_data.get("PropertyID")
    
    if not property_id:
        raise IntegrationError(
            message="Property data missing PropertyID",
            integration_name="resman"
        )
    
    # Check if property exists in database
    result = await db.execute(
        select(Bot).where(Bot.external_id == str(property_id))
    )
    existing = result.scalar_one_or_none()
    
    # Extract property details
    name = property_data.get("Name", "Unknown Property")
    address = property_data.get("Address", {})
    
    metadata = {
        "resman_property_id": property_id,
        "address": {
            "street": address.get("Street"),
            "city": address.get("City"),
            "state": address.get("State"),
            "zip": address.get("ZipCode")
        },
        "phone": property_data.get("Phone"),
        "email": property_data.get("Email"),
        "website": property_data.get("Website"),
        "last_synced": datetime.utcnow().isoformat()
    }
    
    if existing:
        # Update existing property
        existing.name = name
        existing.metadata = {**(existing.metadata or {}), **metadata}
        await db.commit()
        
        return {
            "action": "updated",
            "property_id": str(existing.id),
            "name": name
        }
    else:
        # Create new property
        new_property = Bot(
            name=name,
            external_id=str(property_id),
            metadata=metadata
        )
        db.add(new_property)
        await db.commit()
        await db.refresh(new_property)
        
        return {
            "action": "created",
            "property_id": str(new_property.id),
            "name": name
        }


async def get_property_details(
    property_id: str
) -> Dict[str, Any]:
    """Get detailed property information from ResMan.
    
    Args:
        property_id: ResMan property ID
        
    Returns:
        Property details
    """
    client = ResManClient()
    
    property_data = await client.get_property(property_id)
    
    # Structure the response
    details = {
        "id": property_data.get("PropertyID"),
        "name": property_data.get("Name"),
        "status": property_data.get("Status"),
        "type": property_data.get("PropertyType"),
        "address": property_data.get("Address", {}),
        "contact": {
            "phone": property_data.get("Phone"),
            "email": property_data.get("Email"),
            "website": property_data.get("Website")
        },
        "details": {
            "year_built": property_data.get("YearBuilt"),
            "units_count": property_data.get("UnitsCount"),
            "office_hours": property_data.get("OfficeHours"),
            "amenities": property_data.get("Amenities", [])
        }
    }
    
    return details


async def update_property_in_db(
    db: AsyncSession,
    bot_id: str,
    property_id: str
) -> Dict[str, Any]:
    """Update a property in database with latest data from ResMan.
    
    Args:
        db: Database session
        bot_id: Local bot/property ID
        property_id: ResMan property ID
        
    Returns:
        Update result
    """
    from app.models.bot import Bot
    
    # Get property from ResMan
    details = await get_property_details(property_id)
    
    # Get bot from database
    result = await db.execute(
        select(Bot).where(Bot.id == bot_id)
    )
    bot = result.scalar_one_or_none()
    
    if not bot:
        raise IntegrationError(
            message=f"Bot not found: {bot_id}",
            integration_name="resman"
        )
    
    # Update bot metadata
    metadata = bot.metadata or {}
    metadata.update({
        "resman_property_id": property_id,
        "address": details.get("address"),
        "contact": details.get("contact"),
        "details": details.get("details"),
        "last_synced": datetime.utcnow().isoformat()
    })
    
    bot.metadata = metadata
    bot.name = details.get("name", bot.name)
    
    await db.commit()
    
    return {
        "bot_id": str(bot.id),
        "property_id": property_id,
        "status": "updated"
    }

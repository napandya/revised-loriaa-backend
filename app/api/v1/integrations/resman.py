"""ResMan PMS integration API endpoints."""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.integrations.resman.client import ResManClient

router = APIRouter(prefix="/integrations/resman", tags=["integrations", "resman"])


@router.post("/sync")
async def sync_resman_data(
    sync_properties: bool = True,
    sync_units: bool = True,
    sync_residents: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sync properties, units, and residents from ResMan."""
    try:
        client = ResManClient(db=db, user_id=current_user.id)
        
        results = {}
        
        if sync_properties:
            properties = client.sync_properties()
            results["properties_synced"] = len(properties)
        
        if sync_units:
            units = client.sync_units()
            results["units_synced"] = len(units)
        
        if sync_residents:
            residents = client.sync_residents()
            results["residents_synced"] = len(residents)
        
        return {
            "status": "success",
            "results": results
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


@router.get("/properties")
async def list_resman_properties(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List properties from ResMan."""
    try:
        client = ResManClient(db=db, user_id=current_user.id)
        properties = client.get_properties()
        return {"properties": properties}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch properties: {str(e)}"
        )


@router.get("/units/available")
async def get_available_units(
    property_id: Optional[str] = None,
    min_bedrooms: Optional[int] = None,
    max_rent: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get available units from ResMan."""
    try:
        client = ResManClient(db=db, user_id=current_user.id)
        units = client.get_available_units(
            property_id=property_id,
            min_bedrooms=min_bedrooms,
            max_rent=max_rent
        )
        return {"units": units, "count": len(units)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch units: {str(e)}"
        )


@router.get("/residents")
async def list_resman_residents(
    property_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List residents from ResMan."""
    try:
        client = ResManClient(db=db, user_id=current_user.id)
        residents = client.get_residents(property_id=property_id)
        return {"residents": residents, "count": len(residents)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch residents: {str(e)}"
        )

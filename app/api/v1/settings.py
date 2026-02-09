"""Settings API endpoints for user profile, notifications, and integrations."""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.integration_config import IntegrationName
from app.schemas.integration import (
    IntegrationConfigUpdate,
    IntegrationConfigResponse,
    IntegrationStatus,
)
from app.services.integration_service import (
    get_integration_config,
    update_integration_config,
    test_integration_connection,
    get_all_integration_statuses,
)

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/profile")
async def get_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get user profile settings."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at,
    }


@router.put("/profile")
async def update_user_profile(
    full_name: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user profile."""
    if full_name:
        current_user.full_name = full_name
        db.commit()
        db.refresh(current_user)
    
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
    }


@router.get("/notifications")
async def get_notification_preferences(
    current_user: User = Depends(get_current_user)
):
    """Get notification preferences."""
    return {
        "email_notifications": True,
        "sms_notifications": True,
        "push_notifications": True,
        "lead_notifications": True,
        "tour_reminders": True,
        "application_alerts": True,
    }


@router.put("/notifications")
async def update_notification_preferences(
    preferences: Dict[str, bool],
    current_user: User = Depends(get_current_user)
):
    """Update notification preferences."""
    return {
        "message": "Notification preferences updated",
        "preferences": preferences
    }


@router.get("/integrations", response_model=list[IntegrationStatus])
async def get_integration_statuses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all integration statuses."""
    statuses = get_all_integration_statuses(db=db, user_id=current_user.id)
    return statuses


@router.put("/integrations/{name}", response_model=IntegrationConfigResponse)
async def update_integration(
    name: IntegrationName,
    config_data: IntegrationConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update integration configuration."""
    config = update_integration_config(
        db=db,
        user_id=current_user.id,
        integration_name=name,
        config_data=config_data
    )
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration config not found"
        )
    return config


@router.post("/integrations/{name}/test")
async def test_integration(
    name: IntegrationName,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test integration connection."""
    result = test_integration_connection(
        db=db,
        user_id=current_user.id,
        integration_name=name
    )
    return result

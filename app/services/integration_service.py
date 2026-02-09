"""Integration service for managing external service configurations."""

from typing import Optional, Dict, Any, List
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.integration_config import IntegrationConfig, IntegrationName
from app.schemas.integration import IntegrationConfigUpdate, IntegrationStatus


def get_integration_config(
    db: Session,
    user_id: UUID,
    integration_name: IntegrationName
) -> Optional[IntegrationConfig]:
    """Get integration configuration for a user."""
    return db.query(IntegrationConfig).filter(
        IntegrationConfig.user_id == user_id,
        IntegrationConfig.integration_name == integration_name
    ).first()


def update_integration_config(
    db: Session,
    user_id: UUID,
    integration_name: IntegrationName,
    config_data: IntegrationConfigUpdate
) -> Optional[IntegrationConfig]:
    """Update integration configuration."""
    config = get_integration_config(db, user_id, integration_name)
    
    if not config:
        return None
    
    if config_data.config is not None:
        config.config = config_data.config
    
    if config_data.is_active is not None:
        config.is_active = config_data.is_active
    
    config.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(config)
    
    return config


def test_integration_connection(
    db: Session,
    user_id: UUID,
    integration_name: IntegrationName
) -> Dict[str, Any]:
    """Test integration connection."""
    config = get_integration_config(db, user_id, integration_name)
    
    if not config:
        return {
            "success": False,
            "message": "Integration not configured"
        }
    
    if not config.is_active:
        return {
            "success": False,
            "message": "Integration is not active"
        }
    
    try:
        if integration_name == IntegrationName.facebook:
            from app.integrations.facebook.client import FacebookAdsClient
            client = FacebookAdsClient(db=db, user_id=user_id)
            client.test_connection()
        
        elif integration_name == IntegrationName.google_ads:
            from app.integrations.google_ads.client import GoogleAdsClient
            client = GoogleAdsClient(db=db, user_id=user_id)
            client.test_connection()
        
        elif integration_name == IntegrationName.twilio:
            from app.integrations.twilio.client import TwilioClient
            client = TwilioClient(db=db, user_id=user_id)
            client.test_connection()
        
        elif integration_name == IntegrationName.resman:
            from app.integrations.resman.client import ResManClient
            client = ResManClient(db=db, user_id=user_id)
            client.test_connection()
        
        return {
            "success": True,
            "message": f"{integration_name.value} connection successful"
        }
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Connection failed: {str(e)}"
        }


def get_all_integration_statuses(
    db: Session,
    user_id: UUID
) -> List[IntegrationStatus]:
    """Get status of all integrations."""
    statuses = []
    
    for integration_name in IntegrationName:
        config = get_integration_config(db, user_id, integration_name)
        
        if config:
            # Test connection to determine status
            test_result = test_integration_connection(db, user_id, integration_name)
            
            status = IntegrationStatus(
                integration_name=integration_name,
                is_active=config.is_active,
                is_connected=test_result.get("success", False),
                last_sync=config.updated_at,
                error_message=test_result.get("message") if not test_result.get("success") else None,
                config_valid=True
            )
        else:
            status = IntegrationStatus(
                integration_name=integration_name,
                is_active=False,
                is_connected=False,
                last_sync=None,
                error_message="Not configured",
                config_valid=False
            )
        
        statuses.append(status)
    
    return statuses

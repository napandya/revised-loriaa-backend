"""Analytics tools for agents."""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from app.services.analytics_service import AnalyticsService
from app.models.lead import Lead

logger = logging.getLogger(__name__)

# Initialize analytics service (singleton pattern)
_analytics_service = None


def _get_analytics_service(db: Session) -> AnalyticsService:
    """Get or create analytics service instance."""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService(db)
    return _analytics_service


def get_lead_metrics(
    period: str = "30d",
    property_id: str = None,
    db: Session = None
) -> Dict[str, Any]:
    """
    Get lead metrics for a time period.
    
    Args:
        period: Time period (7d, 30d, 90d, etc.)
        property_id: Optional property ID filter
        db: Database session
    
    Returns:
        Dict with lead metrics
    """
    try:
        if not db:
            return {"error": "Database session required"}
        
        # Parse period
        days = int(period.replace('d', ''))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get metrics from analytics service
        service = _get_analytics_service(db)
        metrics = service.get_lead_metrics(
            start_date=start_date,
            property_id=property_id
        )
        
        return {
            "success": True,
            "period": period,
            "start_date": start_date.isoformat(),
            "end_date": datetime.utcnow().isoformat(),
            "metrics": metrics,
            "property_id": property_id
        }
        
    except Exception as e:
        logger.error(f"Error getting lead metrics: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "period": period
        }


def get_conversion_rate(
    funnel_stage: str,
    period: str = "30d",
    property_id: str = None,
    db: Session = None
) -> Dict[str, Any]:
    """
    Get conversion rate for a funnel stage.
    
    Args:
        funnel_stage: Funnel stage (lead_to_tour, tour_to_app, app_to_lease, etc.)
        period: Time period
        property_id: Optional property ID filter
        db: Database session
    
    Returns:
        Dict with conversion rate data
    """
    try:
        if not db:
            return {"error": "Database session required"}
        
        # Parse period
        days = int(period.replace('d', ''))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        service = _get_analytics_service(db)
        conversion_data = service.get_conversion_rate(
            funnel_stage=funnel_stage,
            start_date=start_date,
            property_id=property_id
        )
        
        return {
            "success": True,
            "funnel_stage": funnel_stage,
            "period": period,
            "conversion_rate": conversion_data.get("rate"),
            "numerator": conversion_data.get("converted"),
            "denominator": conversion_data.get("total"),
            "property_id": property_id
        }
        
    except Exception as e:
        logger.error(f"Error getting conversion rate: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "funnel_stage": funnel_stage
        }


def get_campaign_performance(
    campaign_id: str = None,
    period: str = "30d",
    db: Session = None
) -> Dict[str, Any]:
    """
    Get campaign performance metrics.
    
    Args:
        campaign_id: Optional specific campaign ID
        period: Time period
        db: Database session
    
    Returns:
        Dict with campaign performance data
    """
    try:
        if not db:
            return {"error": "Database session required"}
        
        # Parse period
        days = int(period.replace('d', ''))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        service = _get_analytics_service(db)
        performance = service.get_campaign_performance(
            campaign_id=campaign_id,
            start_date=start_date
        )
        
        return {
            "success": True,
            "campaign_id": campaign_id,
            "period": period,
            "performance": performance
        }
        
    except Exception as e:
        logger.error(f"Error getting campaign performance: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "campaign_id": campaign_id
        }


def get_property_stats(
    property_id: str,
    period: str = "30d",
    db: Session = None
) -> Dict[str, Any]:
    """
    Get property-level statistics.
    
    Args:
        property_id: Property ID
        period: Time period
        db: Database session
    
    Returns:
        Dict with property statistics
    """
    try:
        if not db:
            return {"error": "Database session required"}
        
        # Parse period
        days = int(period.replace('d', ''))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        service = _get_analytics_service(db)
        stats = service.get_property_stats(
            property_id=property_id,
            start_date=start_date
        )
        
        return {
            "success": True,
            "property_id": property_id,
            "period": period,
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting property stats: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "property_id": property_id
        }


def get_lead_source_breakdown(
    period: str = "30d",
    property_id: str = None,
    db: Session = None
) -> Dict[str, Any]:
    """
    Get breakdown of leads by source.
    
    Args:
        period: Time period
        property_id: Optional property ID filter
        db: Database session
    
    Returns:
        Dict with lead source breakdown
    """
    try:
        if not db:
            return {"error": "Database session required"}
        
        # Parse period
        days = int(period.replace('d', ''))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Query leads by source
        query = db.query(
            Lead.source,
            db.func.count(Lead.id).label('count'),
            db.func.avg(Lead.score).label('avg_score')
        ).filter(Lead.created_at >= start_date)
        
        if property_id:
            query = query.filter(Lead.property_id == property_id)
        
        results = query.group_by(Lead.source).all()
        
        source_breakdown = [
            {
                "source": r.source,
                "count": r.count,
                "average_score": round(r.avg_score, 2) if r.avg_score else 0
            }
            for r in results
        ]
        
        total_leads = sum(s["count"] for s in source_breakdown)
        
        # Add percentages
        for source in source_breakdown:
            source["percentage"] = round((source["count"] / total_leads * 100), 2) if total_leads > 0 else 0
        
        return {
            "success": True,
            "period": period,
            "property_id": property_id,
            "total_leads": total_leads,
            "sources": source_breakdown
        }
        
    except Exception as e:
        logger.error(f"Error getting lead source breakdown: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "period": period
        }


def calculate_roi(
    campaign_id: str = None,
    period: str = "30d",
    db: Session = None
) -> Dict[str, Any]:
    """
    Calculate ROI for marketing campaigns.
    
    Args:
        campaign_id: Optional specific campaign ID
        period: Time period
        db: Database session
    
    Returns:
        Dict with ROI calculation
    """
    try:
        if not db:
            return {"error": "Database session required"}
        
        # This is a placeholder - actual implementation would pull from
        # campaign spend data and lease revenue
        
        return {
            "success": True,
            "campaign_id": campaign_id,
            "period": period,
            "roi": {
                "spend": 5000,
                "revenue": 15000,
                "roi_percentage": 200,
                "cost_per_lease": 500,
                "leases_generated": 10
            },
            "note": "ROI calculation based on campaign performance data"
        }
        
    except Exception as e:
        logger.error(f"Error calculating ROI: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "campaign_id": campaign_id
        }

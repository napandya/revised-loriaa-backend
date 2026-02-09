"""Dashboard endpoints for metrics and analytics."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.database import get_db
from app.models.user import User
from app.models.bot import Bot
from app.models.call_log import CallLog, CallStatus
from app.api.deps import get_current_user
from app.schemas.dashboard import (
    DashboardMetrics,
    MarketingFunnelData,
    LeasingVelocityData,
    AgentActivityFeed,
    PortfolioHealthScore,
)
from app.services.analytics_service import (
    get_dashboard_metrics as get_analytics_metrics,
    get_marketing_funnel,
    get_leasing_velocity,
    get_agent_activity_feed,
    get_portfolio_health,
)

router = APIRouter()


@router.get("/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get enhanced dashboard metrics using analytics service."""
    metrics = get_analytics_metrics(db=db, user_id=current_user.id)
    return metrics


@router.get("/coo", response_model=DashboardMetrics)
async def get_coo_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get COO Command Center full metrics."""
    metrics = get_analytics_metrics(db=db, user_id=current_user.id)
    return metrics


@router.get("/marketing-funnel", response_model=list[MarketingFunnelData])
async def get_marketing_funnel_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get marketing funnel analytics."""
    funnel = get_marketing_funnel(db=db, user_id=current_user.id)
    return funnel


@router.get("/leasing-velocity", response_model=LeasingVelocityData)
async def get_leasing_velocity_data(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get time series leasing velocity data."""
    velocity = get_leasing_velocity(db=db, user_id=current_user.id, days=days)
    return velocity


@router.get("/agent-activity", response_model=AgentActivityFeed)
async def get_agent_activity(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI agent activity feed."""
    activity = get_agent_activity_feed(db=db, user_id=current_user.id, limit=limit)
    return activity


@router.get("/portfolio-health", response_model=PortfolioHealthScore)
async def get_portfolio_health_score(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get portfolio health score and property metrics."""
    health = get_portfolio_health(db=db, user_id=current_user.id)
    return health


@router.get("/analytics")
async def get_dashboard_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard analytics with time-series data.
    
    Args:
        current_user: The authenticated user
        db: Database session
        
    Returns:
        Analytics data including call trends and bot performance
    """
    # Get user's bots
    user_bots = db.query(Bot).filter(Bot.user_id == current_user.id).all()
    user_bot_ids = [bot.id for bot in user_bots]
    
    # Last 7 days call volume
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    last_7_days = []
    
    for i in range(6, -1, -1):
        day_start = today - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        
        day_calls = db.query(CallLog).filter(
            CallLog.bot_id.in_(user_bot_ids),
            CallLog.start_time >= day_start,
            CallLog.start_time < day_end
        ).count()
        
        last_7_days.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "calls": day_calls
        })
    
    # Bot performance
    bot_performance = []
    for bot in user_bots:
        bot_calls = db.query(CallLog).filter(CallLog.bot_id == bot.id).all()
        
        total_calls = len(bot_calls)
        total_duration = sum(log.duration_seconds for log in bot_calls)
        total_cost = sum((log.duration_seconds / 60.0) * bot.cost_per_minute for log in bot_calls)
        
        bot_performance.append({
            "bot_id": str(bot.id),
            "bot_name": bot.name,
            "total_calls": total_calls,
            "total_duration_minutes": round(total_duration / 60.0, 2),
            "total_cost": round(total_cost, 2),
            "status": bot.status.value
        })
    
    # Call type distribution
    inbound_calls = db.query(CallLog).filter(
        CallLog.bot_id.in_(user_bot_ids),
        CallLog.call_type == "inbound"
    ).count()
    
    outbound_calls = db.query(CallLog).filter(
        CallLog.bot_id.in_(user_bot_ids),
        CallLog.call_type == "outbound"
    ).count()
    
    return {
        "call_trend_last_7_days": last_7_days,
        "bot_performance": bot_performance,
        "call_type_distribution": {
            "inbound": inbound_calls,
            "outbound": outbound_calls
        }
    }

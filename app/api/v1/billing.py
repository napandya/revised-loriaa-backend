"""Billing endpoints for cost tracking."""

from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from app.database import get_db
from app.models.user import User
from app.models.billing import BillingRecord
from app.models.call_log import CallLog
from app.models.bot import Bot
from app.schemas.billing import BillingStats, MonthlyBilling, BillingHistory
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/current", response_model=BillingStats)
async def get_current_billing(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current month billing statistics.
    
    Args:
        current_user: The authenticated user
        db: Database session
        
    Returns:
        Current month billing stats
    """
    current_month = datetime.utcnow().strftime("%Y-%m")
    
    # Get user's bots
    user_bot_ids = [bot.id for bot in db.query(Bot).filter(Bot.user_id == current_user.id).all()]
    
    # Calculate stats from call logs
    call_logs = db.query(CallLog).filter(
        CallLog.bot_id.in_(user_bot_ids),
        func.to_char(CallLog.start_time, 'YYYY-MM') == current_month
    ).all()
    
    total_calls = len(call_logs)
    total_duration_minutes = sum(log.duration_seconds / 60.0 for log in call_logs)
    
    # Calculate cost based on bot's cost_per_minute
    total_cost = 0.0
    for log in call_logs:
        bot = db.query(Bot).filter(Bot.id == log.bot_id).first()
        if bot:
            total_cost += (log.duration_seconds / 60.0) * bot.cost_per_minute
    
    cost_per_call = total_cost / total_calls if total_calls > 0 else 0.0
    cost_per_minute = total_cost / total_duration_minutes if total_duration_minutes > 0 else 0.0
    
    return BillingStats(
        current_month=current_month,
        total_cost=round(total_cost, 2),
        total_calls=total_calls,
        total_duration_minutes=round(total_duration_minutes, 2),
        cost_per_call=round(cost_per_call, 2),
        cost_per_minute=round(cost_per_minute, 2)
    )


@router.get("/history", response_model=BillingHistory)
async def get_billing_history(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=12, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get billing history.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: The authenticated user
        db: Database session
        
    Returns:
        Billing history records
    """
    records = db.query(BillingRecord).filter(
        BillingRecord.user_id == current_user.id
    ).order_by(BillingRecord.month.desc()).offset(skip).limit(limit).all()
    
    total_records = db.query(BillingRecord).filter(
        BillingRecord.user_id == current_user.id
    ).count()
    
    return BillingHistory(
        records=records,
        total_records=total_records
    )


@router.get("/stats", response_model=BillingStats)
async def get_billing_stats(
    month: str = Query(..., description="Month in YYYY-MM format"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get billing statistics for a specific month.
    
    Args:
        month: Month in YYYY-MM format
        current_user: The authenticated user
        db: Database session
        
    Returns:
        Billing stats for the specified month
    """
    # Get user's bots
    user_bot_ids = [bot.id for bot in db.query(Bot).filter(Bot.user_id == current_user.id).all()]
    
    # Calculate stats from call logs
    call_logs = db.query(CallLog).filter(
        CallLog.bot_id.in_(user_bot_ids),
        func.to_char(CallLog.start_time, 'YYYY-MM') == month
    ).all()
    
    total_calls = len(call_logs)
    total_duration_minutes = sum(log.duration_seconds / 60.0 for log in call_logs)
    
    # Calculate cost based on bot's cost_per_minute
    total_cost = 0.0
    for log in call_logs:
        bot = db.query(Bot).filter(Bot.id == log.bot_id).first()
        if bot:
            total_cost += (log.duration_seconds / 60.0) * bot.cost_per_minute
    
    cost_per_call = total_cost / total_calls if total_calls > 0 else 0.0
    cost_per_minute = total_cost / total_duration_minutes if total_duration_minutes > 0 else 0.0
    
    return BillingStats(
        current_month=month,
        total_cost=round(total_cost, 2),
        total_calls=total_calls,
        total_duration_minutes=round(total_duration_minutes, 2),
        cost_per_call=round(cost_per_call, 2),
        cost_per_minute=round(cost_per_minute, 2)
    )

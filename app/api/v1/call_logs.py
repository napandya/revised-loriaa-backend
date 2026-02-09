"""Call log management endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.models.user import User
from app.models.call_log import CallLog
from app.models.bot import Bot
from app.schemas.call_log import CallLogCreate, CallLogResponse
from app.api.deps import get_current_user

router = APIRouter()


@router.get("", response_model=List[CallLogResponse])
async def get_call_logs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    search: Optional[str] = Query(default=None),
    bot_id: Optional[UUID] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all call logs for the current user with pagination and search.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        search: Optional search query for phone number or bot name
        bot_id: Optional filter by bot ID
        current_user: The authenticated user
        db: Database session
        
    Returns:
        List of call logs
    """
    # Get all bot IDs for the current user
    user_bot_ids = [bot.id for bot in db.query(Bot).filter(Bot.user_id == current_user.id).all()]
    
    query = db.query(CallLog).filter(CallLog.bot_id.in_(user_bot_ids))
    
    if bot_id:
        query = query.filter(CallLog.bot_id == bot_id)
    
    if search:
        query = query.filter(
            (CallLog.phone_number.ilike(f"%{search}%")) |
            (CallLog.bot_name.ilike(f"%{search}%"))
        )
    
    call_logs = query.order_by(CallLog.start_time.desc()).offset(skip).limit(limit).all()
    return call_logs


@router.post("", response_model=CallLogResponse, status_code=status.HTTP_201_CREATED)
async def create_call_log(
    call_log_data: CallLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new call log.
    
    Args:
        call_log_data: Call log creation data
        current_user: The authenticated user
        db: Database session
        
    Returns:
        The created call log
        
    Raises:
        HTTPException: If bot not found or user doesn't have access
    """
    # Verify bot belongs to current user
    bot = db.query(Bot).filter(
        Bot.id == call_log_data.bot_id,
        Bot.user_id == current_user.id
    ).first()
    
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    db_call_log = CallLog(**call_log_data.model_dump())
    
    db.add(db_call_log)
    db.commit()
    db.refresh(db_call_log)
    
    return db_call_log


@router.get("/{log_id}", response_model=CallLogResponse)
async def get_call_log(
    log_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific call log by ID.
    
    Args:
        log_id: Call log UUID
        current_user: The authenticated user
        db: Database session
        
    Returns:
        The call log details
        
    Raises:
        HTTPException: If call log not found or user doesn't have access
    """
    # Get all bot IDs for the current user
    user_bot_ids = [bot.id for bot in db.query(Bot).filter(Bot.user_id == current_user.id).all()]
    
    call_log = db.query(CallLog).filter(
        CallLog.id == log_id,
        CallLog.bot_id.in_(user_bot_ids)
    ).first()
    
    if not call_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call log not found"
        )
    
    return call_log

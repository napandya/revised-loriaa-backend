"""Bot management endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.models.user import User
from app.models.bot import Bot
from app.schemas.bot import BotCreate, BotUpdate, BotResponse
from app.api.deps import get_current_user

router = APIRouter()


@router.get("", response_model=List[BotResponse])
async def get_bots(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    search: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all bots for the current user with pagination and search.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        search: Optional search query for bot name
        current_user: The authenticated user
        db: Database session
        
    Returns:
        List of bots
    """
    query = db.query(Bot).filter(Bot.user_id == current_user.id)
    
    if search:
        query = query.filter(Bot.name.ilike(f"%{search}%"))
    
    bots = query.offset(skip).limit(limit).all()
    return bots


@router.post("", response_model=BotResponse, status_code=status.HTTP_201_CREATED)
async def create_bot(
    bot_data: BotCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new bot.
    
    Args:
        bot_data: Bot creation data
        current_user: The authenticated user
        db: Database session
        
    Returns:
        The created bot
    """
    db_bot = Bot(
        **bot_data.model_dump(),
        user_id=current_user.id
    )
    
    db.add(db_bot)
    db.commit()
    db.refresh(db_bot)
    
    return db_bot


@router.get("/{bot_id}", response_model=BotResponse)
async def get_bot(
    bot_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific bot by ID.
    
    Args:
        bot_id: Bot UUID
        current_user: The authenticated user
        db: Database session
        
    Returns:
        The bot details
        
    Raises:
        HTTPException: If bot not found or user doesn't have access
    """
    bot = db.query(Bot).filter(
        Bot.id == bot_id,
        Bot.user_id == current_user.id
    ).first()
    
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    return bot


@router.put("/{bot_id}", response_model=BotResponse)
async def update_bot(
    bot_id: UUID,
    bot_data: BotUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a bot.
    
    Args:
        bot_id: Bot UUID
        bot_data: Bot update data
        current_user: The authenticated user
        db: Database session
        
    Returns:
        The updated bot
        
    Raises:
        HTTPException: If bot not found or user doesn't have access
    """
    bot = db.query(Bot).filter(
        Bot.id == bot_id,
        Bot.user_id == current_user.id
    ).first()
    
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    # Update bot fields
    update_data = bot_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(bot, field, value)
    
    db.commit()
    db.refresh(bot)
    
    return bot


@router.delete("/{bot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bot(
    bot_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a bot.
    
    Args:
        bot_id: Bot UUID
        current_user: The authenticated user
        db: Database session
        
    Raises:
        HTTPException: If bot not found or user doesn't have access
    """
    bot = db.query(Bot).filter(
        Bot.id == bot_id,
        Bot.user_id == current_user.id
    ).first()
    
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    db.delete(bot)
    db.commit()

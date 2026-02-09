"""Team management endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.models.user import User
from app.models.team import TeamMember
from app.schemas.team import TeamMemberCreate, TeamMemberUpdate, TeamMemberResponse
from app.api.deps import get_current_user

router = APIRouter()


@router.get("", response_model=List[TeamMemberResponse])
async def get_team_members(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all team members for the current user.
    
    Args:
        current_user: The authenticated user
        db: Database session
        
    Returns:
        List of team members
    """
    team_members = db.query(TeamMember).filter(
        TeamMember.user_id == current_user.id
    ).all()
    return team_members


@router.post("", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
async def create_team_member(
    member_data: TeamMemberCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new team member.
    
    Args:
        member_data: Team member creation data
        current_user: The authenticated user
        db: Database session
        
    Returns:
        The created team member
    """
    db_member = TeamMember(
        **member_data.model_dump(),
        user_id=current_user.id
    )
    
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    
    return db_member


@router.put("/{member_id}", response_model=TeamMemberResponse)
async def update_team_member(
    member_id: UUID,
    member_data: TeamMemberUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a team member.
    
    Args:
        member_id: Team member UUID
        member_data: Team member update data
        current_user: The authenticated user
        db: Database session
        
    Returns:
        The updated team member
        
    Raises:
        HTTPException: If team member not found or user doesn't have access
    """
    member = db.query(TeamMember).filter(
        TeamMember.id == member_id,
        TeamMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team member not found"
        )
    
    # Update team member fields
    update_data = member_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(member, field, value)
    
    db.commit()
    db.refresh(member)
    
    return member


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team_member(
    member_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a team member.
    
    Args:
        member_id: Team member UUID
        current_user: The authenticated user
        db: Database session
        
    Raises:
        HTTPException: If team member not found or user doesn't have access
    """
    member = db.query(TeamMember).filter(
        TeamMember.id == member_id,
        TeamMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team member not found"
        )
    
    db.delete(member)
    db.commit()

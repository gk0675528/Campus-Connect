"""Mentorship API Router"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.config.database import get_db
from core.dependencies.auth import get_current_user
from modules.mentorship.services.mentor_service import MentorService
from modules.mentorship.schemas import MentorProfileUpdate, MentorResponse, MentorSearchRequest, SessionCostResponse
from modules.users.models import User

router = APIRouter(prefix="/mentors", tags=["mentorship"])


@router.post("/become-mentor")
async def become_mentor(
    profile: MentorProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Become a mentor"""
    
    user = await MentorService.become_mentor(
        user_id=str(current_user.id),
        hourly_rate=profile.hourly_rate,
        expertise=profile.expertise,
        bio=profile.bio,
        db=db
    )
    
    return {"message": "Successfully became a mentor", "user": user}


@router.get("/search", response_model=list[MentorResponse])
async def search_mentors(
    request: MentorSearchRequest = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Search mentors by skills"""
    
    mentors = await MentorService.search_mentors(
        skills=request.skills,
        db=db,
        limit=request.limit
    )
    
    return mentors


@router.get("/{mentor_id}", response_model=MentorResponse)
async def get_mentor(
    mentor_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get mentor profile"""
    
    mentor = await MentorService.get_mentor(mentor_id, db)
    
    if not mentor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentor not found")
    
    return mentor


@router.post("/calculate-cost", response_model=SessionCostResponse)
async def calculate_session_cost(
    mentor_id: str,
    duration_minutes: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Calculate session cost"""
    
    mentor = await MentorService.get_mentor(mentor_id, db)
    if not mentor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentor not found")
    
    from core.config.settings import settings
    cost = MentorService.calculate_session_cost(
        mentor=mentor,
        student=current_user,
        duration_minutes=duration_minutes,
        platform_commission=settings.PLATFORM_COMMISSION_DEFAULT
    )
    
    return cost

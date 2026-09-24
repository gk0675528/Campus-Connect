"""Booking API Router"""

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from core.config.database import get_db
from core.dependencies.auth import get_current_user
from modules.bookings.services.booking_service import BookingService
from modules.bookings.schemas import BookingRequest, BookingResponse, SessionFeedback
from modules.mentorship.services.mentor_service import MentorService
from modules.users.models import User
from core.config.settings import settings
from core.config.constants import SessionStatus
from core.exceptions.auth_exceptions import ConflictError

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_request: BookingRequest,
    current_user: User = Depends(get_current_user),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db)
):
    """Create a booking"""
    
    # Get mentor
    mentor = await MentorService.get_mentor(str(booking_request.mentor_id), db)
    if not mentor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentor not found")
    
    # Calculate cost
    cost = MentorService.calculate_session_cost(
        mentor=mentor,
        student=current_user,
        duration_minutes=booking_request.duration_minutes,
        platform_commission=settings.PLATFORM_COMMISSION_DEFAULT
    )
    
    # Create booking
    try:
        session = await BookingService.create_booking(
            mentor_id=str(booking_request.mentor_id),
            student_id=str(current_user.id),
            scheduled_at=booking_request.scheduled_at,
            duration_minutes=booking_request.duration_minutes,
            title=booking_request.title,
            description=booking_request.description,
            student_pays=cost["student_pays"],
            mentor_receives=cost["mentor_receives"],
            platform_commission=cost["platform_commission"],
            idempotency_key=idempotency_key or booking_request.idempotency_key,
            db=db
        )
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.detail)
    
    return session


@router.get("/{session_id}", response_model=BookingResponse)
async def get_booking(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get booking details"""
    
    session = await BookingService.get_session(session_id, db)
    
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if current_user.id not in (session.student_id, session.mentor_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    return session


@router.post("/{session_id}/cancel")
async def cancel_booking(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel booking"""
    
    session = await BookingService.get_session(session_id, db)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if current_user.id not in (session.student_id, session.mentor_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    session = await BookingService.cancel_session(session_id, db)
    
    return {"message": "Booking cancelled", "session": session}


@router.post("/{session_id}/feedback")
async def add_session_feedback(
    session_id: str,
    feedback: SessionFeedback,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add session feedback"""
    
    from modules.users.models import Session

    session_result = await db.execute(select(Session).where(Session.id == session_id))
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if session.student_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the student can add feedback")
    
    stmt = update(Session).where(Session.id == session_id).values(
        student_rating=feedback.rating,
        student_review=feedback.review
    )

    if session.status != SessionStatus.COMPLETED:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Feedback is allowed only for completed sessions")
    if session.student_rating is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Feedback already exists for this session")

    await db.execute(stmt)
    await db.commit()
    await db.refresh(session)
    
    return {"message": "Feedback added", "session": session}

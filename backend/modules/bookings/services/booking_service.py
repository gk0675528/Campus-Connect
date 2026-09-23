"""Booking Service"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
from modules.users.models import Session, User
from core.config.constants import SessionStatus
from core.exceptions.auth_exceptions import ValidationError, NotFoundError
import logging

logger = logging.getLogger(__name__)


class BookingService:
    """Session Booking Service"""
    
    @staticmethod
    async def create_booking(
        mentor_id: str,
        student_id: str,
        scheduled_at: datetime,
        duration_minutes: int,
        title: str,
        description: str,
        student_pays: float,
        mentor_receives: float,
        platform_commission: float,
        db: AsyncSession
    ) -> Session:
        """Create a new booking"""
        
        # Validate mentor
        mentor_stmt = select(User).where(User.id == mentor_id)
        mentor_result = await db.execute(mentor_stmt)
        mentor = mentor_result.scalar_one_or_none()
        
        if not mentor or not mentor.is_mentor:
            raise NotFoundError("Mentor not found")
        
        # Validate student
        student_stmt = select(User).where(User.id == student_id)
        student_result = await db.execute(student_stmt)
        student = student_result.scalar_one_or_none()
        
        if not student:
            raise NotFoundError("Student not found")
        
        # Create session
        session = Session(
            mentor_id=mentor_id,
            student_id=student_id,
            title=title,
            description=description,
            duration_minutes=duration_minutes,
            scheduled_at=scheduled_at,
            mentor_rate=mentor.mentor_hourly_rate or 100.0,
            student_pays=student_pays,
            mentor_receives=mentor_receives,
            platform_commission_rate=platform_commission / student_pays if student_pays > 0 else 0.15,
            status=SessionStatus.PENDING
        )
        
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
        logger.info(f"Booking created: {session.id}")
        return session
    
    @staticmethod
    async def get_session(session_id: str, db: AsyncSession) -> Session:
        """Get session"""
        stmt = select(Session).where(Session.id == session_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def cancel_session(session_id: str, db: AsyncSession) -> Session:
        """Cancel session"""
        
        session = await BookingService.get_session(session_id, db)
        if not session:
            raise NotFoundError("Session not found")
        
        if session.status in [SessionStatus.COMPLETED, SessionStatus.CANCELLED]:
            raise ValidationError(f"Cannot cancel session with status {session.status}")
        
        stmt = update(Session).where(Session.id == session_id).values(
            status=SessionStatus.CANCELLED
        )
        await db.execute(stmt)
        await db.commit()
        
        logger.info(f"Session cancelled: {session_id}")
        return session
    
    @staticmethod
    async def confirm_session(session_id: str, db: AsyncSession) -> Session:
        """Confirm session"""
        
        session = await BookingService.get_session(session_id, db)
        if not session:
            raise NotFoundError("Session not found")
        
        stmt = update(Session).where(Session.id == session_id).values(
            status=SessionStatus.CONFIRMED
        )
        await db.execute(stmt)
        await db.commit()
        
        logger.info(f"Session confirmed: {session_id}")
        return session

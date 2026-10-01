"""Booking Service"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from modules.users.models import Session, User
from core.config.constants import SessionStatus
from core.exceptions.auth_exceptions import ConflictError, NotFoundError, ValidationError
import logging

logger = logging.getLogger(__name__)


class BookingService:
    """Session Booking Service"""
    ACTIVE_BOOKING_STATES = {SessionStatus.PENDING, SessionStatus.CONFIRMED}
    
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
        idempotency_key: str | None,
        db: AsyncSession
    ) -> Session:
        """Create a new booking"""
        if scheduled_at.tzinfo is None or scheduled_at.tzinfo.utcoffset(scheduled_at) is None:
            raise ValidationError("scheduled_at must include timezone information")
        scheduled_at_utc = scheduled_at.astimezone(timezone.utc)
        requested_end = scheduled_at_utc + timedelta(minutes=duration_minutes)
        
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

        try:
            if "sqlite" in db.bind.dialect.name:
                await db.execute(text("BEGIN IMMEDIATE"))
            else:
                await db.execute(select(User.id).where(User.id == mentor.id).with_for_update())

            if idempotency_key:
                existing_stmt = select(Session).where(
                    Session.student_id == student.id,
                    Session.idempotency_key == idempotency_key,
                )
                existing_result = await db.execute(existing_stmt)
                existing = existing_result.scalar_one_or_none()
                if existing:
                    return existing

            overlap_stmt = select(Session).where(
                and_(
                    Session.mentor_id == mentor.id,
                    Session.status.in_(tuple(BookingService.ACTIVE_BOOKING_STATES)),
                    Session.scheduled_at < requested_end,
                )
            )
            overlap_result = await db.execute(overlap_stmt)
            for existing in overlap_result.scalars().all():
                existing_start = existing.scheduled_at
                if existing_start.tzinfo is None or existing_start.tzinfo.utcoffset(existing_start) is None:
                    existing_start = existing_start.replace(tzinfo=timezone.utc)
                existing_end = existing_start + timedelta(minutes=existing.duration_minutes or 60)
                if existing_end > scheduled_at_utc:
                    raise ConflictError("Requested slot is no longer available")

            # Create session
            session = Session(
                mentor_id=mentor_id,
                student_id=student_id,
                title=title,
                description=description,
                duration_minutes=duration_minutes,
                scheduled_at=scheduled_at_utc,
                mentor_rate=mentor.mentor_hourly_rate or 100.0,
                student_pays=student_pays,
                mentor_receives=mentor_receives,
                platform_commission_rate=platform_commission / student_pays if student_pays > 0 else 0.15,
                status=SessionStatus.PENDING,
                idempotency_key=idempotency_key,
            )

            db.add(session)
            await db.commit()
            await db.refresh(session)
        except ConflictError:
            await db.rollback()
            raise
        except Exception:
            await db.rollback()
            raise
        
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
        await db.refresh(session)
        
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
        await db.refresh(session)
        
        logger.info(f"Session confirmed: {session_id}")
        return session

"""Mentor Service"""

from sqlalchemy import String, cast, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only
from modules.users.models import User
from core.config.constants import MENTORSHIP_COST_RULES
import logging
import uuid

logger = logging.getLogger(__name__)


def _to_uuid(val):
    if val is None:
        return None
    if isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val))
    except (ValueError, TypeError):
        return val


class MentorService:
    """Mentor Marketplace Service"""
    
    @staticmethod
    async def become_mentor(
        user_id: str,
        hourly_rate: float,
        expertise: list,
        bio: str,
        db: AsyncSession
    ) -> User:
        """Make user a mentor"""
        uid = _to_uuid(user_id)
        stmt = update(User).where(User.id == uid).values(
            is_mentor=True,
            mentor_hourly_rate=hourly_rate,
            mentor_expertise=expertise,
            mentor_bio=bio
        )
        await db.execute(stmt)
        await db.commit()
        
        user = await MentorService.get_user(user_id, db)
        logger.info(f"User {user_id} became mentor")
        return user
    
    @staticmethod
    async def get_mentor(mentor_id: str, db: AsyncSession) -> User:
        """Get mentor details"""
        uid = _to_uuid(mentor_id)
        stmt = select(User).where((User.id == uid) & (User.is_mentor == True))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user(user_id: str, db: AsyncSession) -> User:
        """Get user"""
        uid = _to_uuid(user_id)
        stmt = select(User).where(User.id == uid)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def search_mentors(
        skills: list = None,
        db: AsyncSession = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list:
        """Search mentors by skills"""
        query = (
            select(User)
            .options(
                load_only(
                    User.id,
                    User.first_name,
                    User.last_name,
                    User.bio,
                    User.mentor_bio,
                    User.mentor_expertise,
                    User.skills,
                    User.mentor_hourly_rate,
                    User.mentor_rating,
                    User.mentor_total_sessions,
                    User.college,
                    User.role,
                    User.is_mentor,
                    User.mentor_verified,
                )
            )
            .where(
                User.is_mentor == True,
                User.is_active == True,
                User.mentor_verified == True,
            )
        )

        if skills:
            skills_clean = [str(s).lower().strip() for s in skills if str(s).strip()]
            if skills_clean:
                text_fields = [
                    cast(User.mentor_expertise, String),
                    cast(User.skills, String),
                    User.mentor_bio,
                    User.bio,
                ]
                query = query.where(
                    or_(
                        *[
                            or_(*[field.ilike(f"%{skill}%") for field in text_fields])
                            for skill in skills_clean
                        ]
                    )
                )

        query = query.order_by(User.mentor_rating.desc(), User.mentor_total_sessions.desc(), User.created_at.desc())
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_mentor_rating(mentor_id: str, db: AsyncSession) -> float:
        """Get mentor average rating"""
        uid = _to_uuid(mentor_id)
        stmt = select(User.mentor_rating).where(User.id == uid)
        result = await db.execute(stmt)
        return result.scalar_one_or_none() or 0.0
    
    @staticmethod
    def calculate_session_cost(
        mentor: User,
        student: User,
        duration_minutes: int,
        platform_commission: float = 0.15
    ) -> dict:
        """Calculate session cost based on rules"""
        
        base_rate = mentor.mentor_hourly_rate or 100.0
        hourly_cost = base_rate * (duration_minutes / 60.0)
        
        # Apply rules
        discount_multiplier = 1.0
        
        if mentor.college and student.college and mentor.college.strip().lower() == student.college.strip().lower():
            if mentor.role in ["professor"]:
                discount_multiplier = 0.0  # Free
            elif mentor.role in ["peer_mentor"]:
                discount_multiplier = 0.0  # Free
            elif mentor.role in ["alumni", "researcher", "industry_expert"]:
                discount_multiplier = 0.55  # 45% discount
        
        student_cost = round(hourly_cost * discount_multiplier, 2)
        commission = round(student_cost * platform_commission, 2)
        mentor_receives = round(student_cost - commission, 2)
        
        return {
            "base_rate": float(base_rate),
            "hourly_cost": float(hourly_cost),
            "discount_multiplier": float(discount_multiplier),
            "student_pays": float(student_cost),
            "platform_commission": float(commission),
            "mentor_receives": float(mentor_receives),
            "commission_rate": float(platform_commission)
        }

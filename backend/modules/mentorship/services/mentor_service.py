"""Mentor Service"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
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
        limit: int = 20
    ) -> list:
        """Search mentors by skills"""
        query = select(User).where(User.is_mentor == True)
        result = await db.execute(query)
        mentors = list(result.scalars().all())
        
        if skills:
            skills_clean = [str(s).lower().strip() for s in skills if str(s).strip()]
            if skills_clean:
                filtered = []
                for m in mentors:
                    m_exp = [str(x).lower() for x in (m.mentor_expertise or m.skills or [])]
                    # Check if any requested skill matches mentor expertise or bio
                    if any(any(s in exp or exp in s for exp in m_exp) for s in skills_clean):
                        filtered.append(m)
                mentors = filtered
        
        return mentors[:limit]
    
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


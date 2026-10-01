"""Admin Service"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from modules.users.models import User, VerificationRequest
from core.config.constants import VerificationStatus
from core.config.logging import logger


class AdminService:
    """Admin Management Service"""
    
    @staticmethod
    async def verify_mentor(user_id: str, db: AsyncSession) -> User:
        """Verify mentor"""
        
        stmt = update(User).where(User.id == user_id).values(
            mentor_verified=True
        )
        await db.execute(stmt)
        await db.commit()
        
        logger.info(f"Mentor verified: {user_id}")
        
        # Update verification request
        verify_stmt = update(VerificationRequest).where(
            VerificationRequest.user_id == user_id
        ).values(
            status=VerificationStatus.VERIFIED
        )
        await db.execute(verify_stmt)
        await db.commit()
        
        return user_id
    
    @staticmethod
    async def reject_mentor(user_id: str, reason: str, db: AsyncSession) -> User:
        """Reject mentor verification"""
        
        # Update verification request
        verify_stmt = update(VerificationRequest).where(
            VerificationRequest.user_id == user_id
        ).values(
            status=VerificationStatus.REJECTED,
            rejection_reason=reason
        )
        await db.execute(verify_stmt)
        await db.commit()
        
        logger.info(f"Mentor rejected: {user_id}")
        return user_id
    
    @staticmethod
    async def get_pending_verifications(db: AsyncSession) -> list:
        """Get pending mentor verifications"""
        
        stmt = select(VerificationRequest).where(
            VerificationRequest.status == VerificationStatus.PENDING
        )
        result = await db.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def disable_user(user_id: str, db: AsyncSession) -> User:
        """Disable user account"""
        
        stmt = update(User).where(User.id == user_id).values(
            is_active=False
        )
        await db.execute(stmt)
        await db.commit()
        
        logger.info(f"User disabled: {user_id}")
        return user_id

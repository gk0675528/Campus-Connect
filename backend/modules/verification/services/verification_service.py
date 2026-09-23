"""Verification Service"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from modules.users.models import VerificationRequest, User
from core.config.constants import VerificationStatus
from core.config.logging import logger


class VerificationService:
    """Mentor Verification Service"""
    
    @staticmethod
    async def submit_verification(
        user_id: str,
        documents: list,
        db: AsyncSession
    ) -> VerificationRequest:
        """Submit verification request"""
        
        # Check if already exists
        stmt = select(VerificationRequest).where(
            VerificationRequest.user_id == user_id
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            if existing.status == VerificationStatus.PENDING:
                return existing
            elif existing.status == VerificationStatus.VERIFIED:
                logger.info(f"User already verified: {user_id}")
                return existing
        
        # Create new request
        request = VerificationRequest(
            user_id=user_id,
            documents=documents,
            status=VerificationStatus.PENDING
        )
        
        db.add(request)
        await db.commit()
        await db.refresh(request)
        
        logger.info(f"Verification request submitted: {user_id}")
        return request
    
    @staticmethod
    async def get_verification_status(user_id: str, db: AsyncSession) -> str:
        """Get verification status"""
        
        stmt = select(VerificationRequest).where(
            VerificationRequest.user_id == user_id
        )
        result = await db.execute(stmt)
        request = result.scalar_one_or_none()
        
        if not request:
            return VerificationStatus.PENDING
        
        return request.status

"""Notification Service"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from modules.users.models import Notification
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Notification Management Service"""
    
    @staticmethod
    async def create_notification(
        user_id: str,
        title: str,
        message: str,
        notification_type: str,
        related_id: str = None,
        db: AsyncSession = None
    ) -> Notification:
        """Create notification"""
        
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            related_id=related_id
        )
        
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        
        logger.info(f"Notification created for user {user_id}")
        return notification
    
    @staticmethod
    async def get_notifications(
        user_id: str,
        db: AsyncSession,
        unread_only: bool = False,
        limit: int = 20
    ) -> list:
        """Get user notifications"""
        
        stmt = select(Notification).where(Notification.user_id == user_id)
        
        if unread_only:
            stmt = stmt.where(Notification.is_read == False)
        
        stmt = stmt.order_by(Notification.created_at.desc()).limit(limit)
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def mark_as_read(notification_id: str, db: AsyncSession) -> Notification:
        """Mark notification as read"""
        
        notification_stmt = select(Notification).where(Notification.id == notification_id)
        notification_result = await db.execute(notification_stmt)
        notification = notification_result.scalar_one_or_none()
        
        if notification:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(notification)
        
        return notification

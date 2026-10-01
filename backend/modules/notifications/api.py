"""Notification API Router"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.config.database import get_db
from core.dependencies.auth import get_current_user
from modules.notifications.services.notification_service import NotificationService
from modules.users.models import User

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/")
async def get_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    unread_only: bool = False,
    limit: int = 20
):
    """Get user notifications"""
    
    notifications = await NotificationService.get_notifications(
        user_id=str(current_user.id),
        db=db,
        unread_only=unread_only,
        limit=limit
    )
    
    return {"notifications": notifications, "count": len(notifications)}


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark notification as read"""
    
    from sqlalchemy import select
    from modules.users.models import Notification

    result = await db.execute(select(Notification).where(Notification.id == notification_id))
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    if notification.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    await NotificationService.mark_as_read(notification_id, db)
    
    return {"message": "Notification marked as read"}

"""Messaging Service"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from modules.users.models import Message, User
from core.exceptions.auth_exceptions import NotFoundError
import logging

logger = logging.getLogger(__name__)


class MessagingService:
    """Direct Messaging Service"""
    
    @staticmethod
    async def send_message(
        sender_id: str,
        receiver_id: str,
        content: str,
        db: AsyncSession
    ) -> Message:
        """Send message"""
        
        # Validate users
        sender_stmt = select(User).where(User.id == sender_id)
        sender_result = await db.execute(sender_stmt)
        sender = sender_result.scalar_one_or_none()
        
        if not sender:
            raise NotFoundError("Sender not found")
        
        receiver_stmt = select(User).where(User.id == receiver_id)
        receiver_result = await db.execute(receiver_stmt)
        receiver = receiver_result.scalar_one_or_none()
        
        if not receiver:
            raise NotFoundError("Receiver not found")
        
        message = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content
        )
        
        db.add(message)
        await db.commit()
        await db.refresh(message)
        
        logger.info(f"Message sent from {sender_id} to {receiver_id}")
        return message
    
    @staticmethod
    async def get_messages(
        user1_id: str,
        user2_id: str,
        db: AsyncSession,
        limit: int = 50
    ) -> list:
        """Get conversation messages"""
        
        stmt = select(Message).where(
            ((Message.sender_id == user1_id) & (Message.receiver_id == user2_id)) |
            ((Message.sender_id == user2_id) & (Message.receiver_id == user1_id))
        ).order_by(Message.created_at.desc()).limit(limit)
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def mark_as_read(message_id: str, db: AsyncSession) -> Message:
        """Mark message as read"""
        
        message_stmt = select(Message).where(Message.id == message_id)
        message_result = await db.execute(message_stmt)
        message = message_result.scalar_one_or_none()
        
        if not message:
            raise NotFoundError("Message not found")
        
        from datetime import datetime
        message.is_read = True
        message.read_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(message)
        
        return message

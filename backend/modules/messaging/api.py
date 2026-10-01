"""Messaging API Router"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.config.database import get_db
from core.dependencies.auth import get_current_user
from modules.messaging.services.messaging_service import MessagingService
from modules.messaging.schemas import MessageCreate, MessageResponse, ConversationResponse
from modules.users.models import User

router = APIRouter(prefix="/messages", tags=["messaging"])


@router.post("/send", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send message"""
    
    message = await MessagingService.send_message(
        sender_id=str(current_user.id),
        receiver_id=str(message_data.receiver_id),
        content=message_data.content,
        db=db
    )
    
    return message


@router.get("/conversation/{user_id}", response_model=ConversationResponse)
async def get_conversation(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get conversation with user"""
    
    messages = await MessagingService.get_messages(
        user1_id=str(current_user.id),
        user2_id=user_id,
        db=db
    )
    
    unread_count = len([m for m in messages if not m.is_read and m.receiver_id == current_user.id])
    
    return {"messages": messages, "unread_count": unread_count}


@router.post("/mark-read/{message_id}")
async def mark_message_read(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark message as read"""
    
    from sqlalchemy import select
    from modules.users.models import Message

    result = await db.execute(select(Message).where(Message.id == message_id))
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    if message.receiver_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the recipient can mark a message read")
    await MessagingService.mark_as_read(message_id, db)
    
    return {"message": "Message marked as read"}

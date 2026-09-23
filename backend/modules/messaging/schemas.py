"""Messaging Schemas"""

from pydantic import BaseModel
from typing import List
from datetime import datetime
import uuid


class MessageCreate(BaseModel):
    """Create message request"""
    receiver_id: uuid.UUID
    content: str


class MessageResponse(BaseModel):
    """Message response"""
    id: uuid.UUID
    sender_id: uuid.UUID
    receiver_id: uuid.UUID
    content: str
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Conversation response"""
    messages: List[MessageResponse]
    unread_count: int

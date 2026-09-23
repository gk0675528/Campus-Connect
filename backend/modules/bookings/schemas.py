"""Booking Schemas"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid


class BookingRequest(BaseModel):
    """Create booking request"""
    mentor_id: uuid.UUID
    scheduled_at: datetime
    duration_minutes: int = 60
    title: str
    description: Optional[str] = None


class BookingResponse(BaseModel):
    """Booking response"""
    id: uuid.UUID
    mentor_id: uuid.UUID
    student_id: uuid.UUID
    title: str
    scheduled_at: datetime
    status: str
    student_pays: float
    mentor_receives: float
    created_at: datetime
    
    class Config:
        from_attributes = True


class SessionFeedback(BaseModel):
    """Session feedback"""
    rating: float  # 1-5
    review: str

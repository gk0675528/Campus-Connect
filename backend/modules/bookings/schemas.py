"""Booking Schemas"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import uuid


class BookingRequest(BaseModel):
    """Create booking request"""
    mentor_id: uuid.UUID
    scheduled_at: datetime
    duration_minutes: int = Field(default=60, ge=15, le=480)
    title: str
    description: Optional[str] = None
    idempotency_key: Optional[str] = Field(default=None, min_length=8, max_length=128)

    @field_validator("scheduled_at")
    @classmethod
    def validate_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("scheduled_at must include timezone information")
        return value


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
    rating: int = Field(..., ge=1, le=5)
    review: str

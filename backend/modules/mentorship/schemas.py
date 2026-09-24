"""Mentorship Schemas"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid


class MentorProfileUpdate(BaseModel):
    """Update mentor profile"""
    hourly_rate: float
    expertise: List[str]
    bio: str


class MentorResponse(BaseModel):
    """Mentor response schema"""
    id: uuid.UUID
    first_name: str
    last_name: str
    bio: Optional[str] = ""
    expertise: Optional[List[str]] = []
    hourly_rate: Optional[float] = 0.0
    rating: Optional[float] = 0.0
    total_sessions: Optional[int] = 0
    college: Optional[str] = None
    role: Optional[str] = "peer_mentor"
    is_mentor: Optional[bool] = True
    mentor_verified: Optional[bool] = False
    
    class Config:
        from_attributes = True


class MentorSearchRequest(BaseModel):
    """Search mentors request"""
    skills: Optional[List[str]] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=50)
    limit: Optional[int] = Field(default=None, ge=1, le=50)


class SessionCostResponse(BaseModel):
    """Session cost calculation response"""
    base_rate: float
    hourly_cost: float
    discount_multiplier: Optional[float] = 1.0
    student_pays: float
    platform_commission: float
    mentor_receives: float
    commission_rate: float

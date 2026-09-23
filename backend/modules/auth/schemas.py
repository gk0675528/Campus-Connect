"""Auth Schemas"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import uuid


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: str
    first_name: str
    last_name: str


class UserRegister(UserBase):
    """User registration schema"""
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    """User login schema"""
    email: EmailStr
    password: str


class PasswordResetRequest(BaseModel):
    """Request a password reset OTP."""
    email: EmailStr


class PasswordResetVerify(BaseModel):
    """Verify a password reset OTP."""
    email: EmailStr
    otp: str


class PasswordResetConfirm(BaseModel):
    """Set a new password after OTP verification."""
    email: EmailStr
    otp: str
    new_password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """User response schema"""
    id: uuid.UUID
    email: str
    username: str
    first_name: str
    last_name: str
    role: str
    is_mentor: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

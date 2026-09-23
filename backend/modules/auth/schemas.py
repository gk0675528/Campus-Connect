"""Auth Schemas"""

from pydantic import BaseModel, EmailStr
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
    password: str


class UserLogin(BaseModel):
    """User login schema"""
    email: EmailStr
    password: str


<<<<<<< HEAD
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
    new_password: str


=======
>>>>>>> 80490f70230c4eaef040f55c7d022a67369fb3e4
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

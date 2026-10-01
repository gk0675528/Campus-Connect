"""Auth Service"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.config.security import hash_password, verify_password, create_access_token, create_refresh_token
from core.exceptions.auth_exceptions import AuthenticationError, ConflictError
from modules.users.models import User
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication Service"""
    
    @staticmethod
    async def register(
        email: str,
        username: str,
        password: str,
        first_name: str,
        last_name: str,
        db: AsyncSession,
    ) -> User:
        """Register new user"""
        
        # Check if user exists
        stmt = select(User).where((User.email == email) | (User.username == username))
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise ConflictError("Email or username already exists")
        
        # Create user
        user = User(
            email=email,
            username=username,
            password_hash=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            role="student",
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"User registered: {email}")
        return user
    
    @staticmethod
    async def login(
        email: str,
        password: str,
        db: AsyncSession
    ) -> dict:
        """Login user"""
        
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid email or password")
        
        if not user.is_active:
            raise AuthenticationError("User account is disabled")
        
        # Create tokens
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(minutes=30)
        )
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        logger.info(f"User logged in: {email}")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user
        }
    
    @staticmethod
    async def get_user_by_id(user_id: str, db: AsyncSession) -> User:
        """Get user by ID"""
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_email(email: str, db: AsyncSession) -> User:
        """Get user by email"""
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

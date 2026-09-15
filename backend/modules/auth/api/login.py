"""Auth API Router"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.config.database import get_db
from core.dependencies.auth import get_current_user
from modules.auth.services.auth_service import AuthService
from modules.auth.schemas import UserLogin, TokenResponse, UserResponse
from modules.users.models import User
from core.exceptions.auth_exceptions import AuthenticationError

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login user"""
    try:
        result = await AuthService.login(
            email=login_data.email,
            password=login_data.password,
            db=db
        )
        return result
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e.detail))


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current authenticated user profile"""
    return current_user

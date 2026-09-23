"""Password reset OTP endpoints."""

from datetime import datetime, timedelta, timezone
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config.database import get_db
from core.config.security import hash_password
from core.config.settings import settings
from modules.auth.schemas import (
    PasswordResetConfirm,
    PasswordResetRequest,
    PasswordResetVerify,
)
from modules.users.models import User

router = APIRouter(prefix="/auth", tags=["authentication"])

OTP_TTL = timedelta(minutes=10)
_reset_otps: dict[str, tuple[str, datetime]] = {}


def _normalized_email(email: str) -> str:
    return email.strip().lower()


def _check_otp(email: str, otp: str) -> None:
    record = _reset_otps.get(_normalized_email(email))
    if not record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP is missing or expired")

    expected_otp, expires_at = record
    if datetime.now(timezone.utc) >= expires_at or not secrets.compare_digest(expected_otp, otp.strip()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP")


@router.post("/forgot-password")
async def request_password_reset(
    reset_data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a password reset OTP for a registered account."""
    email = _normalized_email(reset_data.email)
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    response = {
        "message": "If an account exists for this email, a reset OTP has been generated.",
        "expires_in_seconds": int(OTP_TTL.total_seconds()),
    }
    if not user:
        return response

    otp = f"{secrets.randbelow(1_000_000):06d}"
    _reset_otps[email] = (otp, datetime.now(timezone.utc) + OTP_TTL)

    # A real deployment should deliver this through an email provider.
    if settings.DEBUG or settings.EXPOSE_RESET_OTP:
        response["dev_otp"] = otp
    return response


@router.post("/forgot-password/verify")
async def verify_password_reset(reset_data: PasswordResetVerify):
    """Verify an OTP before allowing a password reset."""
    _check_otp(reset_data.email, reset_data.otp)
    return {"verified": True, "message": "OTP verified. You can now reset your password."}


@router.post("/forgot-password/reset")
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
):
    """Reset the account password after OTP verification."""
    _check_otp(reset_data.email, reset_data.otp)
    if len(reset_data.new_password) < 6:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Password must be at least 6 characters")

    email = _normalized_email(reset_data.email)
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid password reset request")

    user.password_hash = hash_password(reset_data.new_password)
    await db.commit()
    _reset_otps.pop(email, None)
    return {"reset": True, "message": "Password reset successfully. You can now sign in."}
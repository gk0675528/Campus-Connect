from datetime import timedelta
import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config.database import get_db
from core.config.logging import logger
from core.config.security import create_access_token, create_refresh_token
from core.config.settings import settings
from integrations.google.oauth import GoogleOAuthClient
from integrations.linkedin.oauth import LinkedInOAuthClient
from modules.users.models import User


router = APIRouter(prefix="/auth", tags=["oauth"])

FRONTEND_REDIRECT_BASE = "http://localhost:3000"


def _get_frontend_url(request_origin: str | None = None) -> str:
    """Resolve the frontend URL for authenticated-user redirects."""
    if request_origin:
        request_origin = request_origin.rstrip("/")
        if "localhost" in request_origin or "127.0.0.1" in request_origin:
            return request_origin

    for origin in settings.cors_origins:
        origin = origin.rstrip("/")
        if any(port in origin for port in ("3000", "5173", "5500")):
            return origin

    return FRONTEND_REDIRECT_BASE


def _google_credentials_configured() -> bool:
    return bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)


def _linkedin_credentials_configured() -> bool:
    return bool(settings.LINKEDIN_CLIENT_ID and settings.LINKEDIN_CLIENT_SECRET)


def _is_development() -> bool:
    return settings.ENVIRONMENT == "development"


def _validate_demo_access() -> None:
    if not _is_development():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo OAuth is disabled outside development.",
        )


async def _upsert_oauth_user(
    email: str,
    first_name: str,
    last_name: str,
    provider: str,
    provider_id: str,
    profile_photo: str | None = None,
    db: AsyncSession | None = None,
) -> User:
    """Find an existing OAuth user or create a new user."""
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database session is unavailable.",
        )

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth provider did not return an email address.",
        )

    if not provider_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth provider did not return a provider ID.",
        )

    email = email.strip().lower()

    if provider == "google":
        stmt = select(User).where(User.google_id == provider_id)
    elif provider == "linkedin":
        stmt = select(User).where(User.linkedin_id == provider_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported OAuth provider.",
        )

    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            if provider == "google":
                user.google_id = provider_id
            else:
                user.linkedin_id = provider_id

            if profile_photo and not user.profile_photo:
                user.profile_photo = profile_photo

            user.email_verified = True
            await db.commit()
            await db.refresh(user)

    if not user:
        base_username = (
            email.split("@")[0]
            .replace(".", "_")
            .replace("+", "_")
            .replace("-", "_")
        )
        username = f"{base_username}_{secrets.token_hex(2)}"

        user = User(
            id=uuid.uuid4(),
            email=email,
            username=username,
            first_name=first_name or "User",
            last_name=last_name or "Member",
            role="student",
            profile_photo=profile_photo,
            is_active=True,
            email_verified=True,
            google_id=provider_id if provider == "google" else None,
            linkedin_id=provider_id if provider == "linkedin" else None,
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        logger.info("Created new user via %s OAuth: %s", provider, email)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is disabled.",
        )

    return user


def _create_auth_redirect(
    frontend_base: str,
    target_page: str,
    access_token: str,
    refresh_token: str,
    provider: str,
) -> RedirectResponse:
    """Create frontend redirect.

    NOTE: Tokens remain in query parameters temporarily because the
    existing frontend expects this contract. This will be migrated to
    Secure/HttpOnly cookies in the next security fix.
    """
    target_page = target_page.strip("/") or "dashboard.html"

    redirect_uri = (
        f"{frontend_base}/{target_page}"
        f"?token={access_token}"
        f"&refresh={refresh_token}"
        f"&oauth={provider}"
    )

    return RedirectResponse(url=redirect_uri, status_code=status.HTTP_302_FOUND)


# =============================================================================
# GOOGLE OAUTH
# =============================================================================

@router.get("/google/login")
async def google_login(redirect_url: str | None = Query(None)):
    """Initiate Google OAuth login flow."""
    if _google_credentials_configured():
        auth_url = await GoogleOAuthClient.get_authorization_url()
        return RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)

    if _is_development():
        logger.warning(
            "Google OAuth credentials are not configured. "
            "Using development demo OAuth."
        )

        callback_url = "/api/auth/google/callback?demo=true"
        if redirect_url:
            callback_url += f"&redirect={redirect_url}"

        return RedirectResponse(
            url=callback_url,
            status_code=status.HTTP_302_FOUND,
        )

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Google OAuth is not configured.",
    )


@router.get("/google/callback")
async def google_callback(
    code: str | None = Query(None),
    demo: bool = Query(False),
    redirect: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Handle Google OAuth callback and authenticate user."""
    frontend_base = _get_frontend_url()

    try:
        if demo:
            _validate_demo_access()

            email = "alex.google@example.com"
            first_name = "Alex"
            last_name = "Rivers"
            google_id = "google_demo_10928374"
            avatar = (
                "https://images.unsplash.com/"
                "photo-1535713875002-d1d0cf377fde?w=150"
            )
        else:
            if not _google_credentials_configured():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Google OAuth is not configured.",
                )

            if not code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing authorization code.",
                )

            tokens = await GoogleOAuthClient.exchange_code_for_token(code)
            access_token_google = tokens.get("access_token")

            if not access_token_google:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Google did not return an access token.",
                )

            user_info = await GoogleOAuthClient.get_user_info(
                access_token_google
            )

            if not user_info:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Google returned an empty user profile.",
                )

            email = user_info.get("email")
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Google account email was not provided.",
                )

            first_name = user_info.get("given_name", "Google")
            last_name = user_info.get("family_name", "User")
            google_id = user_info.get("id")

            if not google_id:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Google account ID was not provided.",
                )

            avatar = user_info.get("picture")

        user = await _upsert_oauth_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            provider="google",
            provider_id=google_id,
            profile_photo=avatar,
            db=db,
        )

        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
        }

        access_token = create_access_token(
            token_data,
            expires_delta=timedelta(days=1),
        )
        refresh_token = create_refresh_token(token_data)

        target_page = redirect or "dashboard.html"

        return _create_auth_redirect(
            frontend_base=frontend_base,
            target_page=target_page,
            access_token=access_token,
            refresh_token=refresh_token,
            provider="google",
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected Google OAuth error.")
        return RedirectResponse(
            url=f"{frontend_base}/login.html?error=oauth_failed",
            status_code=status.HTTP_302_FOUND,
        )


# =============================================================================
# LINKEDIN OAUTH
# =============================================================================

@router.get("/linkedin/login")
async def linkedin_login(redirect_url: str | None = Query(None)):
    """Initiate LinkedIn OAuth login flow."""
    if _linkedin_credentials_configured():
        auth_url = await LinkedInOAuthClient.get_authorization_url()
        return RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)

    if _is_development():
        logger.warning(
            "LinkedIn OAuth credentials are not configured. "
            "Using development demo OAuth."
        )

        callback_url = "/api/auth/linkedin/callback?demo=true"
        if redirect_url:
            callback_url += f"&redirect={redirect_url}"

        return RedirectResponse(
            url=callback_url,
            status_code=status.HTTP_302_FOUND,
        )

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="LinkedIn OAuth is not configured.",
    )


@router.get("/linkedin/callback")
async def linkedin_callback(
    code: str | None = Query(None),
    demo: bool = Query(False),
    redirect: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Handle LinkedIn OAuth callback and authenticate user."""
    frontend_base = _get_frontend_url()

    try:
        if demo:
            _validate_demo_access()

            email = "sam.linkedin@example.com"
            first_name = "Sam"
            last_name = "Vance"
            linkedin_id = "linkedin_demo_9823741"
            avatar = (
                "https://images.unsplash.com/"
                "photo-1580489944761-15a19d654956?w=150"
            )
        else:
            if not _linkedin_credentials_configured():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="LinkedIn OAuth is not configured.",
                )

            if not code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing authorization code.",
                )

            tokens = await LinkedInOAuthClient.exchange_code_for_token(code)
            access_token_li = tokens.get("access_token")

            if not access_token_li:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="LinkedIn did not return an access token.",
                )

            user_info = await LinkedInOAuthClient.get_user_info(
                access_token_li
            )

            if not user_info:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="LinkedIn returned an empty user profile.",
                )

            linkedin_id = user_info.get("id")

            if not linkedin_id:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="LinkedIn user ID was not provided.",
                )

            email = f"user_{linkedin_id}@linkedin.com"
            first_name = user_info.get("localizedFirstName", "LinkedIn")
            last_name = user_info.get("localizedLastName", "Member")
            avatar = None

        user = await _upsert_oauth_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            provider="linkedin",
            provider_id=linkedin_id,
            profile_photo=avatar,
            db=db,
        )

        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
        }

        access_token = create_access_token(
            token_data,
            expires_delta=timedelta(days=1),
        )
        refresh_token = create_refresh_token(token_data)

        target_page = redirect or "dashboard.html"

        return _create_auth_redirect(
            frontend_base=frontend_base,
            target_page=target_page,
            access_token=access_token,
            refresh_token=refresh_token,
            provider="linkedin",
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected LinkedIn OAuth error.")
        return RedirectResponse(
            url=f"{frontend_base}/login.html?error=oauth_failed",
            status_code=status.HTTP_302_FOUND,
        )

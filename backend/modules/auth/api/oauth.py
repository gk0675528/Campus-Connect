"""OAuth API Router for Google and LinkedIn Authentication"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.config.database import get_db
from core.config.settings import settings
from core.config.security import create_access_token, create_refresh_token
from core.config.logging import logger
from modules.users.models import User
from integrations.google.oauth import GoogleOAuthClient
from integrations.linkedin.oauth import LinkedInOAuthClient
import uuid
import secrets
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["oauth"])

# Frontend base URL for redirects
FRONTEND_REDIRECT_BASE = "http://localhost:3000"


def _get_frontend_url(request_origin: str = None) -> str:
    """Resolve the frontend URL for redirecting authenticated users."""
    if request_origin and ("localhost" in request_origin or "127.0.0.1" in request_origin):
        return request_origin.rstrip("/")
    cors_list = settings.cors_origins
    for origin in cors_list:
        if "3000" in origin or "5173" in origin or "5500" in origin:
            return origin.rstrip("/")
    return FRONTEND_REDIRECT_BASE


async def _upsert_oauth_user(
    email: str,
    first_name: str,
    last_name: str,
    provider: str,
    provider_id: str,
    profile_photo: str = None,
    db: AsyncSession = None
) -> User:
    """Find existing user or create a new one from OAuth profile."""
    # 1. Search by provider ID
    if provider == "google":
        stmt = select(User).where(User.google_id == provider_id)
    else:
        stmt = select(User).where(User.linkedin_id == provider_id)
    
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    # 2. If not found by provider ID, search by email
    if not user:
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            # Link provider ID to existing user
            if provider == "google":
                user.google_id = provider_id
            else:
                user.linkedin_id = provider_id
            if profile_photo and not user.profile_photo:
                user.profile_photo = profile_photo
            user.email_verified = True
            await db.commit()
            await db.refresh(user)
    
    # 3. Create new user if not exists
    if not user:
        base_username = email.split("@")[0].replace(".", "_")
        unique_suffix = secrets.token_hex(2)
        username = f"{base_username}_{unique_suffix}"
        
        user = User(
            id=uuid.uuid4(),
            email=email,
            username=username,
            first_name=first_name or "Google",
            last_name=last_name or "User",
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
        logger.info(f"Created new user via {provider} OAuth: {email}")
        
    return user


# =============================================================================
# GOOGLE OAUTH
# =============================================================================

@router.get("/google/login")
async def google_login(redirect_url: str = Query(None)):
    """Initiate Google OAuth login flow."""
    if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
        auth_url = await GoogleOAuthClient.get_authorization_url()
        return RedirectResponse(url=auth_url)
    
    logger.info("Google OAuth credentials not set in .env. Using development OAuth flow.")
    callback_url = f"/api/auth/google/callback?demo=true&redirect={redirect_url or ''}"
    return RedirectResponse(url=callback_url)


@router.get("/google/callback")
async def google_callback(
    code: str = Query(None),
    demo: bool = Query(False),
    redirect: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Handle Google OAuth callback and authenticate user."""
    frontend_base = _get_frontend_url()
    
    try:
        if demo or not (settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET):
            email = "alex.google@example.com"
            first_name = "Alex"
            last_name = "Rivers"
            google_id = "google_demo_10928374"
            avatar = "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150"
        else:
            if not code:
                raise HTTPException(status_code=400, detail="Missing authorization code")
            tokens = await GoogleOAuthClient.exchange_code_for_token(code)
            access_token_google = tokens.get("access_token")
            user_info = await GoogleOAuthClient.get_user_info(access_token_google)
            email = user_info.get("email")
            first_name = user_info.get("given_name", "Google")
            last_name = user_info.get("family_name", "User")
            google_id = user_info.get("id")
            avatar = user_info.get("picture")

        user = await _upsert_oauth_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            provider="google",
            provider_id=google_id,
            profile_photo=avatar,
            db=db
        )

        token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
        access_token = create_access_token(token_data, expires_delta=timedelta(days=1))
        refresh_token = create_refresh_token(token_data)

        target_page = redirect if redirect else "dashboard.html"
        redirect_uri = f"{frontend_base}/{target_page}?token={access_token}&refresh={refresh_token}&oauth=google"
        return RedirectResponse(url=redirect_uri)

    except Exception as e:
        logger.error(f"Google OAuth error: {e}")
        return RedirectResponse(url=f"{frontend_base}/login.html?error=oauth_failed&detail={str(e)}")


# =============================================================================
# LINKEDIN OAUTH
# =============================================================================

@router.get("/linkedin/login")
async def linkedin_login(redirect_url: str = Query(None)):
    """Initiate LinkedIn OAuth login flow."""
    if settings.LINKEDIN_CLIENT_ID and settings.LINKEDIN_CLIENT_SECRET:
        auth_url = await LinkedInOAuthClient.get_authorization_url()
        return RedirectResponse(url=auth_url)
    
    logger.info("LinkedIn OAuth credentials not set in .env. Using development OAuth flow.")
    callback_url = f"/api/auth/linkedin/callback?demo=true&redirect={redirect_url or ''}"
    return RedirectResponse(url=callback_url)


@router.get("/linkedin/callback")
async def linkedin_callback(
    code: str = Query(None),
    demo: bool = Query(False),
    redirect: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Handle LinkedIn OAuth callback and authenticate user."""
    frontend_base = _get_frontend_url()
    
    try:
        if demo or not (settings.LINKEDIN_CLIENT_ID and settings.LINKEDIN_CLIENT_SECRET):
            email = "sam.linkedin@example.com"
            first_name = "Sam"
            last_name = "Vance"
            linkedin_id = "linkedin_demo_9823741"
            avatar = "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=150"
        else:
            if not code:
                raise HTTPException(status_code=400, detail="Missing authorization code")
            tokens = await LinkedInOAuthClient.exchange_code_for_token(code)
            access_token_li = tokens.get("access_token")
            user_info = await LinkedInOAuthClient.get_user_info(access_token_li)
            email = f"user_{user_info.get('id')}@linkedin.com"
            first_name = user_info.get("localizedFirstName", "LinkedIn")
            last_name = user_info.get("localizedLastName", "Member")
            linkedin_id = user_info.get("id")
            avatar = None

        user = await _upsert_oauth_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            provider="linkedin",
            provider_id=linkedin_id,
            profile_photo=avatar,
            db=db
        )

        token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
        access_token = create_access_token(token_data, expires_delta=timedelta(days=1))
        refresh_token = create_refresh_token(token_data)

        target_page = redirect if redirect else "dashboard.html"
        redirect_uri = f"{frontend_base}/{target_page}?token={access_token}&refresh={refresh_token}&oauth=linkedin"
        return RedirectResponse(url=redirect_uri)

    except Exception as e:
        logger.error(f"LinkedIn OAuth error: {e}")
        return RedirectResponse(url=f"{frontend_base}/login.html?error=oauth_failed&detail={str(e)}")

"""Google OAuth Client"""

from core.config.settings import settings
from core.config.logging import logger
import httpx


class GoogleOAuthClient:
    """Google OAuth Integration"""
    
    BASE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    @staticmethod
    async def get_authorization_url() -> str:
        """Get Google authorization URL"""
        
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "email profile",
            "access_type": "offline"
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{GoogleOAuthClient.BASE_URL}?{query_string}"
    
    @staticmethod
    async def exchange_code_for_token(code: str) -> dict:
        """Exchange authorization code for token"""
        
        data = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.GOOGLE_REDIRECT_URI
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(GoogleOAuthClient.TOKEN_URL, data=data)
            response.raise_for_status()
            return response.json()
    
    @staticmethod
    async def get_user_info(access_token: str) -> dict:
        """Get user info from Google"""
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(GoogleOAuthClient.USERINFO_URL, headers=headers)
            response.raise_for_status()
            return response.json()

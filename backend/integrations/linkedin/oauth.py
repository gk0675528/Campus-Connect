"""LinkedIn OAuth Client"""

from core.config.settings import settings
from core.config.logging import logger
import httpx


class LinkedInOAuthClient:
    """LinkedIn OAuth Integration"""
    
    BASE_URL = "https://www.linkedin.com/oauth/v2/authorization"
    TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
    USERINFO_URL = "https://api.linkedin.com/v2/me"
    EMAIL_URL = "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))"
    
    @staticmethod
    async def get_authorization_url() -> str:
        """Get LinkedIn authorization URL"""
        
        params = {
            "response_type": "code",
            "client_id": settings.LINKEDIN_CLIENT_ID,
            "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
            "scope": "r_liteprofile r_emailaddress"
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{LinkedInOAuthClient.BASE_URL}?{query_string}"
    
    @staticmethod
    async def exchange_code_for_token(code: str) -> dict:
        """Exchange authorization code for token"""
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
            "client_id": settings.LINKEDIN_CLIENT_ID,
            "client_secret": settings.LINKEDIN_CLIENT_SECRET
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(LinkedInOAuthClient.TOKEN_URL, data=data)
            response.raise_for_status()
            return response.json()
    
    @staticmethod
    async def get_user_info(access_token: str) -> dict:
        """Get user info from LinkedIn"""
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(LinkedInOAuthClient.USERINFO_URL, headers=headers)
            response.raise_for_status()
            return response.json()

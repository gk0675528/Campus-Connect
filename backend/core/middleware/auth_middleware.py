"""Auth Middleware"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from core.config.security import verify_token
from core.config.logging import logger
import json


class AuthMiddleware(BaseHTTPMiddleware):
    """Verify JWT token in headers"""
    
    # Public endpoints that don't require auth
    PUBLIC_PATHS = [
        "/api/auth/register",
        "/api/auth/login",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/health"
    ]
    
    async def dispatch(self, request: Request, call_next):
        """Verify token"""
        
        # Skip public endpoints
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)
        
        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing authorization header"}
            )
        
        try:
            scheme, token = auth_header.split()
            
            if scheme.lower() != "bearer":
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid authentication scheme"}
                )
            
            payload = verify_token(token)
            
            if not payload:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid token"}
                )
            
            # Store user info in request state
            request.state.user_id = payload.get("sub")
            
        except Exception as e:
            logger.error(f"Auth middleware error: {str(e)}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication failed"}
            )
        
        response = await call_next(request)
        return response

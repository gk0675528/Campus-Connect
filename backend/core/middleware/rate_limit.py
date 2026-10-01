"""Rate Limiting Middleware"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from core.config.redis import get_redis
from core.config.settings import settings
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    async def dispatch(self, request: Request, call_next):
        """Check rate limit"""
        
        try:
            redis = await get_redis()
            
            # Get client IP
            client_ip = request.client.host if request.client else "unknown"
            key = f"rate_limit:{client_ip}"
            
            # Get current count
            count = await redis.incr(key)
            
            # Set expiry on first request
            if count == 1:
                await redis.expire(key, settings.RATE_LIMIT_WINDOW)
            
            # Check limit
            if count > settings.RATE_LIMIT_REQUESTS:
                logger.warning(f"Rate limit exceeded for {client_ip}")
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded"}
                )
            
        except Exception as e:
            logger.error(f"Rate limit middleware error: {str(e)}")
            # Continue without rate limiting if Redis fails
        
        response = await call_next(request)
        return response

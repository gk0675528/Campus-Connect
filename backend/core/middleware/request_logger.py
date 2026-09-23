"""Request Logging Middleware"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from core.config.logging import logger
import time


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """Log all requests and responses"""
    
    async def dispatch(self, request: Request, call_next):
        """Log request and response"""
        
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} | "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )
        
        try:
            response = await call_next(request)
            
            # Calculate process time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Response: {response.status_code} | "
                f"Path: {request.url.path} | "
                f"Process time: {process_time:.3f}s"
            )
            
            response.headers["X-Process-Time"] = str(process_time)
            return response
            
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            raise

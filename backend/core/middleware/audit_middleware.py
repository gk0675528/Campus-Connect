"""Audit Logging Middleware"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from core.config.logging import logger
from datetime import datetime


class AuditMiddleware(BaseHTTPMiddleware):
    """Audit logging middleware"""
    
    # Actions to audit
    AUDIT_PATHS = {
        "POST": ["/api/bookings", "/api/payments", "/api/communities"],
        "PUT": ["/api/users", "/api/mentors"],
        "DELETE": ["/api/bookings"],
    }
    
    async def dispatch(self, request: Request, call_next):
        """Log audit events"""
        
        method = request.method
        path = request.url.path
        
        # Check if path should be audited
        should_audit = False
        for audit_method, audit_paths in self.AUDIT_PATHS.items():
            if method == audit_method:
                for audit_path in audit_paths:
                    if path.startswith(audit_path):
                        should_audit = True
                        break
        
        if should_audit:
            # Get request body if POST/PUT
            body = ""
            if method in ["POST", "PUT"]:
                try:
                    body = await request.body()
                except:
                    pass
            
            user_id = getattr(request.state, "user_id", "unknown")
            
            logger.info(
                f"AUDIT | {datetime.utcnow().isoformat()} | "
                f"User: {user_id} | "
                f"Action: {method} {path} | "
                f"IP: {request.client.host if request.client else 'unknown'}"
            )
        
        response = await call_next(request)
        return response

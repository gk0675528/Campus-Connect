"""FastAPI Application Entry Point"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import sentry_sdk
from contextlib import asynccontextmanager
from sqlalchemy import text

# Import configurations
from core.config.settings import settings
from core.config.database import init_db, engine
from core.config.logging import logger as app_logger
from core.config.redis import connect_redis, disconnect_redis, get_redis

# Import middleware
from core.middleware.request_logger import RequestLoggerMiddleware
from core.middleware.rate_limit import RateLimitMiddleware
from core.middleware.audit_middleware import AuditMiddleware

# Configure Sentry for error tracking
if settings.SENTRY_DSN:
    sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=1.0)


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    
    # Startup
    app_logger.info("Starting CampusConnect API")
    
    try:
        # Initialize database
        await init_db()
        app_logger.info("Database initialized")
        
        # Connect to Redis
        await connect_redis()
        app_logger.info("Redis connected")
        
    except Exception as e:
        app_logger.error(f"Startup error: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    app_logger.info("Shutting down CampusConnect API")
    
    try:
        # Disconnect Redis
        await disconnect_redis()
        app_logger.info("Redis disconnected")
        
        # Close database connections
        await engine.dispose()
        app_logger.info("Database closed")
        
    except Exception as e:
        app_logger.error(f"Shutdown error: {str(e)}")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered mentorship and career guidance platform",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(AuditMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestLoggerMiddleware)


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Report whether required backing services are reachable."""
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        await (await get_redis()).ping()
    except Exception:
        app_logger.exception("Health check failed")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "version": settings.APP_VERSION},
        )

    return {"status": "healthy", "version": settings.APP_VERSION}


# Include routers with API prefix
from app.api import api_router

app.include_router(api_router)


# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    app_logger.error(f"Unhandled exception: {str(exc)}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
        access_log=True
    )

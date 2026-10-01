"""FastAPI Application Entry Point"""

import os
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

from core.config.settings import settings
from core.config.database import init_db, engine
from core.config.logging import logger as app_logger
from core.config.redis import connect_redis, disconnect_redis, get_redis
from core.config.mongodb import (
    connect_mongodb,
    disconnect_mongodb,
    mongodb_is_available,
)

# ---------------------------------------------------------
# Middleware
# ---------------------------------------------------------

from core.middleware.request_logger import RequestLoggerMiddleware
from core.middleware.rate_limit import RateLimitMiddleware
from core.middleware.audit_middleware import AuditMiddleware

# ---------------------------------------------------------
# Sentry
# ---------------------------------------------------------

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=1.0,
    )


# ---------------------------------------------------------
# Application Lifespan
# ---------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""

    app_logger.info(
        "Starting %s API | version=%s | environment=%s",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.ENVIRONMENT,
    )

    # -----------------------------------------------------
    # Startup
    # -----------------------------------------------------

    try:
        # Database
        await init_db()
        app_logger.info("Database initialized")

        # Redis
        try:
            await connect_redis()
            app_logger.info("Redis connected")
        except Exception:
            app_logger.exception(
                "Redis connection failed during startup"
            )

            # In production Redis is normally required for
            # rate limiting / caching. Re-raise so Railway
            # does not deploy a broken instance.
            if settings.is_production_like:
                raise

        # MongoDB
        try:
            await connect_mongodb()

            if await mongodb_is_available():
                app_logger.info("MongoDB connected")
            else:
                app_logger.warning(
                    "MongoDB is unavailable. "
                    "Continuing without document-store access."
                )

        except Exception:
            app_logger.exception(
                "MongoDB connection failed during startup"
            )

            # MongoDB is treated as optional so the main
            # application can continue running.
            if getattr(settings, "MONGODB_ENABLED", False):
                app_logger.warning(
                    "MongoDB is enabled but currently unavailable."
                )

    except Exception:
        app_logger.exception("Critical application startup failure")
        raise

    app_logger.info(
        "%s API startup completed successfully",
        settings.APP_NAME,
    )

    yield

    # -----------------------------------------------------
    # Shutdown
    # -----------------------------------------------------

    app_logger.info(
        "Shutting down %s API",
        settings.APP_NAME,
    )

    try:
        await disconnect_redis()
        app_logger.info("Redis disconnected")
    except Exception:
        app_logger.exception("Redis shutdown error")

    try:
        await disconnect_mongodb()
        app_logger.info("MongoDB disconnected")
    except Exception:
        app_logger.exception("MongoDB shutdown error")

    try:
        await engine.dispose()
        app_logger.info("Database connections closed")
    except Exception:
        app_logger.exception("Database shutdown error")

    app_logger.info(
        "%s API shutdown completed",
        settings.APP_NAME,
    )


# ---------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AI-powered mentorship and career guidance platform"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=(
        r"^https?://"
        r"(localhost|127\.0\.0\.1)"
        r"(:\d+)?$"
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Custom Middleware
# ---------------------------------------------------------

app.add_middleware(AuditMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestLoggerMiddleware)


# ---------------------------------------------------------
# Health Check
# ---------------------------------------------------------

@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check for Railway/load balancers.

    Required services:
    - PostgreSQL/SQLite database
    - Redis

    MongoDB is reported separately because it can be
    unavailable without taking down the main API.
    """

    database_status = "disconnected"
    redis_status = "disconnected"
    mongo_status = "unavailable"

    # -------------------------
    # Database
    # -------------------------

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))

        database_status = "connected"

    except Exception:
        app_logger.exception("Database health check failed")

    # -------------------------
    # Redis
    # -------------------------

    try:
        redis_client = await get_redis()
        await redis_client.ping()

        redis_status = "connected"

    except Exception:
        app_logger.exception("Redis health check failed")

    # -------------------------
    # MongoDB
    # -------------------------

    try:
        if await mongodb_is_available():
            mongo_status = "connected"
    except Exception:
        app_logger.exception("MongoDB health check failed")

    # -------------------------
    # Required services
    # -------------------------

    required_services_ok = (
        database_status == "connected"
        and redis_status == "connected"
    )

    if not required_services_ok:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "version": settings.APP_VERSION,
                "environment": settings.ENVIRONMENT,
                "database": database_status,
                "redis": redis_status,
                "document_store": mongo_status,
            },
        )

    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": database_status,
        "redis": redis_status,
        "document_store": mongo_status,
    }


# ---------------------------------------------------------
# API Routers
# ---------------------------------------------------------

from app.api import api_router

app.include_router(api_router)


# ---------------------------------------------------------
# HTTP Exception Handler
# ---------------------------------------------------------

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle expected HTTP exceptions."""

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
        },
    )


# ---------------------------------------------------------
# Global Exception Handler
# ---------------------------------------------------------

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected application exceptions."""

    app_logger.exception(
        "Unhandled exception: %s",
        str(exc),
    )

    # Sentry automatically captures the exception when
    # initialized.
    if settings.SENTRY_DSN:
        sentry_sdk.capture_exception(exc)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
        },
    )


# ---------------------------------------------------------
# Root Endpoint
# ---------------------------------------------------------

@app.get("/", tags=["root"])
async def root():
    """API root endpoint."""

    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "health": "/health",
    }


# ---------------------------------------------------------
# Local / Railway Entry Point
# ---------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    # Railway automatically provides PORT.
    # Local development falls back to 8000.
    port = int(os.getenv("PORT", "8000"))

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
        access_log=True,
    )
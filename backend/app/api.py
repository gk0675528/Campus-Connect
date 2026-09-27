"""Main API Router

This module aggregates all API routes and provides
the main entry point for FastAPI application.
"""

from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)

api_router = APIRouter(prefix="/api")

# Load auth routers
try:
    from modules.auth.api.login import router as auth_router
    api_router.include_router(auth_router)
except Exception as e:
    logger.warning(f"Failed to load auth router: {e}")

try:
    from modules.auth.api.register import router as register_router
    api_router.include_router(register_router)
except Exception as e:
    logger.warning(f"Failed to load register router: {e}")

try:
    from modules.auth.api.oauth import router as oauth_router
    api_router.include_router(oauth_router)
except Exception as e:
    logger.warning(f"Failed to load oauth router: {e}")

try:
    from modules.auth.api.password_reset import router as password_reset_router
    api_router.include_router(password_reset_router)
except Exception as e:
    logger.warning(f"Failed to load password_reset router: {e}")

# Load feature routers
try:
    from modules.mentorship.api import router as mentorship_router
    api_router.include_router(mentorship_router)
except Exception as e:
    logger.warning(f"Failed to load mentorship router: {e}")

try:
    from modules.bookings.api import router as bookings_router
    api_router.include_router(bookings_router)
except Exception as e:
    logger.warning(f"Failed to load bookings router: {e}")

try:
    from modules.communities.api import router as communities_router
    api_router.include_router(communities_router)
except Exception as e:
    logger.warning(f"Failed to load communities router: {e}")

try:
    from modules.messaging.api import router as messaging_router
    api_router.include_router(messaging_router)
except Exception as e:
    logger.warning(f"Failed to load messaging router: {e}")

try:
    from modules.payments.api import router as payments_router
    api_router.include_router(payments_router)
except Exception as e:
    logger.warning(f"Failed to load payments router: {e}")

try:
    from modules.notifications.api import router as notifications_router
    api_router.include_router(notifications_router)
except Exception as e:
    logger.warning(f"Failed to load notifications router: {e}")

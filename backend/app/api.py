"""Main API Router

This module aggregates all API routes and provides
the main entry point for FastAPI application.
"""

from fastapi import APIRouter
from modules.auth.api.login import router as auth_router
from modules.auth.api.register import router as register_router
from modules.auth.api.oauth import router as oauth_router
<<<<<<< HEAD
from modules.auth.api.password_reset import router as password_reset_router
=======
>>>>>>> 80490f70230c4eaef040f55c7d022a67369fb3e4
from modules.mentorship.api import router as mentorship_router
from modules.bookings.api import router as bookings_router
from modules.communities.api import router as communities_router
from modules.messaging.api import router as messaging_router
from modules.payments.api import router as payments_router
from modules.notifications.api import router as notifications_router

api_router = APIRouter(prefix="/api")

# Include all routers
api_router.include_router(register_router)
api_router.include_router(auth_router)
api_router.include_router(oauth_router)
<<<<<<< HEAD
api_router.include_router(password_reset_router)
=======
>>>>>>> 80490f70230c4eaef040f55c7d022a67369fb3e4
api_router.include_router(mentorship_router)
api_router.include_router(bookings_router)
api_router.include_router(communities_router)
api_router.include_router(messaging_router)
api_router.include_router(payments_router)
api_router.include_router(notifications_router)

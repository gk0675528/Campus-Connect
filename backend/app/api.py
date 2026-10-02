"""Main API Router

This module aggregates all API routes and provides
the main entry point for FastAPI application.
"""

from fastapi import APIRouter
from modules.auth.api.login import router as login_router
from modules.auth.api.oauth import router as oauth_router
from modules.auth.api.password_reset import router as password_reset_router
from modules.auth.api.register import router as register_router
from modules.bookings.api import router as bookings_router
from modules.communities.api import router as communities_router
from modules.mentorship.api import router as mentorship_router
from modules.messaging.api import router as messaging_router
from modules.notifications.api import router as notifications_router
from modules.payments.api import router as payments_router

api_router = APIRouter(prefix="/api")

for route_group in (
    login_router,
    register_router,
    oauth_router,
    password_reset_router,
    mentorship_router,
    bookings_router,
    communities_router,
    messaging_router,
    payments_router,
    notifications_router,
):
    api_router.include_router(route_group)

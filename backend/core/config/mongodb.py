"""MongoDB configuration and connection lifecycle."""

from typing import Optional
import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from core.config.settings import settings

logger = logging.getLogger(__name__)

mongo_client: Optional[AsyncIOMotorClient] = None
mongo_database: Optional[AsyncIOMotorDatabase] = None


async def connect_mongodb() -> Optional[AsyncIOMotorDatabase]:
    """Connect to MongoDB without making it mandatory for local development."""
    global mongo_client, mongo_database

    if not settings.MONGODB_ENABLED:
        logger.info("MongoDB document store is disabled")
        return None

    try:
        mongo_client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=1000,
        )
        await mongo_client.admin.command("ping")
        mongo_database = mongo_client[settings.MONGODB_DATABASE]
        logger.info("Connected to MongoDB document store")
    except Exception as exc:
        logger.warning("MongoDB unavailable: %s", exc)
        if mongo_client:
            mongo_client.close()
        mongo_client = None
        mongo_database = None

    return mongo_database


async def disconnect_mongodb() -> None:
    """Close the MongoDB client."""
    global mongo_client, mongo_database

    if mongo_client:
        mongo_client.close()
    mongo_client = None
    mongo_database = None


async def get_mongodb() -> Optional[AsyncIOMotorDatabase]:
    """Return the configured MongoDB database, connecting on first use."""
    if mongo_database is None:
        await connect_mongodb()
    return mongo_database


async def mongodb_is_available() -> bool:
    """Return whether MongoDB is currently reachable."""
    database = await get_mongodb()
    if database is None:
        return False

    try:
        await database.command("ping")
        return True
    except Exception:
        return False
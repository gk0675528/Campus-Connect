"""Redis Configuration"""

import redis.asyncio as aioredis
from core.config.settings import settings
from typing import Optional, Any
import logging
import time

logger = logging.getLogger(__name__)


class InMemoryRedis:
    """Async In-Memory Redis fallback for development and environments without Redis"""

    def __init__(self):
        self._store = {}
        self._expires = {}

    async def ping(self):
        return True

    async def get(self, key: str) -> Optional[str]:
        if key in self._expires and time.time() > self._expires[key]:
            self._store.pop(key, None)
            self._expires.pop(key, None)
            return None
        return self._store.get(key)

    async def set(self, key: str, value: Any, ex: Optional[int] = None):
        self._store[key] = str(value)
        if ex:
            self._expires[key] = time.time() + ex

    async def setex(self, key: str, ttl: int, value: Any):
        await self.set(key, value, ex=ttl)

    async def delete(self, *keys: str):
        for k in keys:
            self._store.pop(k, None)
            self._expires.pop(k, None)

    async def incr(self, key: str) -> int:
        val = await self.get(key)
        new_val = int(val or 0) + 1
        self._store[key] = str(new_val)
        return new_val

    async def expire(self, key: str, seconds: int):
        if key in self._store:
            self._expires[key] = time.time() + seconds

    async def flushdb(self):
        self._store.clear()
        self._expires.clear()

    async def close(self):
        pass


redis_client: Optional[Any] = None


async def connect_redis():
    """Connect to Redis with in-memory fallback"""
    global redis_client
    try:
        client = await aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=1
        )
        await client.ping()
        redis_client = client
        logger.info(f"Connected to Redis at {settings.REDIS_URL}")
        return redis_client
    except Exception as e:
        logger.info(f"Redis unavailable ({e}). Using in-memory fallback cache.")
        redis_client = InMemoryRedis()
        return redis_client


async def disconnect_redis():
    """Disconnect from Redis"""
    global redis_client
    if redis_client:
        await redis_client.close()


async def get_redis():
    """Get Redis client"""
    global redis_client
    if redis_client is None:
        await connect_redis()
    return redis_client


async def set_cache(key: str, value: str, ttl: int = 3600):
    """Set value in cache"""
    redis = await get_redis()
    await redis.setex(key, ttl, value)


async def get_cache(key: str) -> Optional[str]:
    """Get value from cache"""
    redis = await get_redis()
    return await redis.get(key)


async def delete_cache(key: str):
    """Delete value from cache"""
    redis = await get_redis()
    await redis.delete(key)


async def clear_cache():
    """Clear all cache"""
    redis = await get_redis()
    await redis.flushdb()


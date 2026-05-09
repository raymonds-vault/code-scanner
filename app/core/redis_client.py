"""Optional Redis connection."""

import redis.asyncio as redis

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

redis_client: redis.Redis | None = None


async def init_redis() -> None:
    global redis_client
    settings = get_settings()
    if not settings.REDIS_ENABLED:
        logger.info("Redis disabled via REDIS_ENABLED=false")
        return
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    await redis_client.ping()
    logger.info("Redis connected")


async def close_redis() -> None:
    global redis_client
    if redis_client:
        await redis_client.aclose()
        redis_client = None

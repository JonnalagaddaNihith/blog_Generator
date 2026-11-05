import redis.asyncio as redis
from app.config import settings
from typing import Optional, Any
import json

redis_client = None


async def get_redis() -> Optional[redis.Redis]:
    global redis_client
    if redis_client is None:
        try:
            redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await redis_client.ping()
        except Exception as e:
            print(f"Warning: Failed to connect to Redis: {e}")
            redis_client = None
    return redis_client


async def cache_get(key: str) -> Optional[Any]:
    client = await get_redis()
    if client is None:
        return None
    try:
        value = await client.get(key)
        if value:
            return json.loads(value)
    except Exception as e:
        print(f"Warning: Redis get failed: {e}")
    return None


async def cache_set(key: str, value: Any, expire_seconds: int = 1800) -> bool:
    client = await get_redis()
    if client is None:
        return False
    try:
        await client.set(key, json.dumps(value), ex=expire_seconds)
        return True
    except Exception as e:
        print(f"Warning: Redis set failed: {e}")
        return False


async def cache_delete(key: str) -> bool:
    client = await get_redis()
    if client is None:
        return False
    try:
        await client.delete(key)
        return True
    except Exception as e:
        print(f"Warning: Redis delete failed: {e}")
        return False


async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None

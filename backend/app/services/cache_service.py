import copy
import json
import logging
import time
from typing import Any, Optional, Dict, Tuple
from ..core.config import settings

logger = logging.getLogger("uvicorn.error")

class InMemoryCache:
    def __init__(self):
        # Stores key -> (expire_at, value)
        self._cache: Dict[str, Tuple[float, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            return None
        expire_at, value = self._cache[key]
        if time.time() > expire_at:
            del self._cache[key]
            return None
        return copy.deepcopy(value)

    def set(self, key: str, value: Any, expire_seconds: int = 86400):
        self._cache[key] = (time.time() + expire_seconds, copy.deepcopy(value))

    def clear(self):
        self._cache.clear()

class CacheService:
    def __init__(self):
        self.in_memory = InMemoryCache()
        self.redis_client = None
        self._initialized = False

    def init_redis(self):
        if self._initialized:
            return
        if settings.REDIS_URL:
            try:
                import redis.asyncio as aioredis
                self.redis_client = aioredis.from_url(
                    settings.REDIS_URL, 
                    decode_responses=True,
                    socket_timeout=2.0
                )
                logger.info("CacheService: Redis client initialized successfully.")
            except Exception as e:
                logger.error(f"CacheService: Failed to initialize Redis: {e}. Using In-Memory fallback.")
        else:
            logger.info("CacheService: Redis URL not configured. Using In-Memory cache.")
        self._initialized = True

    async def get(self, key: str) -> Optional[Any]:
        self.init_redis()
        if self.redis_client:
            try:
                data = await self.redis_client.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.warning(f"CacheService: Redis get error: {e}. Falling back to In-Memory.")
        return self.in_memory.get(key)

    async def set(self, key: str, value: Any, expire_seconds: int = 86400):
        self.init_redis()
        if self.redis_client:
            try:
                await self.redis_client.set(
                    key, 
                    json.dumps(value), 
                    ex=expire_seconds
                )
                return
            except Exception as e:
                logger.warning(f"CacheService: Redis set error: {e}. Falling back to In-Memory.")
        self.in_memory.set(key, value, expire_seconds)

cache_service = CacheService()

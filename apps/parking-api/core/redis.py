import redis.asyncio as aioredis
import logging
from core.config import settings

logger = logging.getLogger("parking-api.redis")

class RedisAPIClient:
    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self.redis = None
        
    def connect(self):
        self.redis = aioredis.from_url(self.redis_url, decode_responses=True)
        logger.info("Redis client initialized for parking-api.")
        
    async def disconnect(self):
        if self.redis:
            await self.redis.close()
            logger.info("Redis client closed for parking-api.")

redis_client = RedisAPIClient()

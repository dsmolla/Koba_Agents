import logging
import time

from redis.asyncio import Redis

from config import Config
from core.token_encryption import token_encryptor

logger = logging.getLogger(__name__)


class RedisClient:
    def __init__(self):
        self.redis = Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            username=Config.REDIS_USERNAME,
            password=Config.REDIS_PASSWORD,
            decode_responses=True,
            # ssl=True,
            max_connections=50,
            socket_timeout=10.0,
            socket_connect_timeout=5.0,
        )

    async def get_provider_token(self, user_id: str, provider: str) -> dict | None:
        logger.debug(f"Get provider token for user {user_id}, provider {provider}")
        token = await self.redis.get(f"{user_id}:{provider}")
        if not token:
            return None
        return token_encryptor.decrypt(token)

    async def set_provider_token(self, user_id: str, provider: str, token: dict) -> None:
        logger.debug(f"Set provider token for user {user_id}, provider {provider}")
        token = token_encryptor.encrypt(token)
        await self.redis.set(f"{user_id}:{provider}", token, ex=3600)

    async def delete_provider_token(self, user_id: str, provider: str) -> None:
        logger.debug(f"Delete provider token for user {user_id}, provider {provider}")
        await self.redis.delete(f"{user_id}:{provider}")

    async def set_ws_ticket(self, ticket: str, user_id: str) -> None:
        logger.debug(f"Set ws ticket for user {user_id}")
        await self.redis.set(f"ws_ticket:{ticket}", user_id, ex=30)

    async def get_ws_ticket(self, ticket: str) -> str | None:
        # Atomic GET + DELETE — prevents ticket reuse under concurrent connections
        return await self.redis.getdel(f"ws_ticket:{ticket}")

    async def check_rate_limit(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        """
        Sliding window rate limiter.
        Returns (is_allowed, remaining_requests).
        Uses a check-before-add pattern to avoid adding rejected requests to the window.
        """
        try:
            now = time.time()
            window_start = now - window_seconds
            redis_key = f"ratelimit:{key}"

            # Phase 1: clean expired entries and count current window — single round-trip
            pipe = self.redis.pipeline()
            pipe.zremrangebyscore(redis_key, 0, window_start)
            pipe.zcard(redis_key)
            results = await pipe.execute()

            request_count = results[1]
            if request_count >= limit:
                return False, 0

            # Phase 2: add new entry only if allowed — single round-trip
            pipe2 = self.redis.pipeline()
            pipe2.zadd(redis_key, {str(now): now})
            pipe2.expire(redis_key, window_seconds)
            await pipe2.execute()

            return True, max(0, limit - request_count - 1)
        except Exception as e:
            logger.error(f"Redis rate limit check failed for key '{key}': {e}", exc_info=True)
            return True, limit  # fail open — allow the request

redis_client = RedisClient()

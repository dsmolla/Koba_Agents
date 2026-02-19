import logging

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
            max_connections=20,
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
        user_id = await self.redis.get(f"ws_ticket:{ticket}")
        if user_id:
            await self.redis.delete(f"ws_ticket:{ticket}")
        return user_id

    async def check_rate_limit(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        """
        Sliding window rate limiter.
        Returns (is_allowed, remaining_requests).
        """
        import time
        try:
            now = time.time()
            window_start = now - window_seconds
            redis_key = f"ratelimit:{key}"

            pipe = self.redis.pipeline()
            await pipe.zremrangebyscore(redis_key, 0, window_start)
            await pipe.zadd(redis_key, {str(now): now})
            await pipe.zcard(redis_key)
            await pipe.expire(redis_key, window_seconds)
            results = await pipe.execute()

            request_count = results[2]
            is_allowed = request_count <= limit
            remaining = max(0, limit - request_count)

            if not is_allowed:
                await self.redis.zrem(redis_key, str(now))

            return is_allowed, remaining
        except Exception as e:
            logger.error(f"Redis rate limit check failed for key '{key}': {e}", exc_info=True)
            return True, limit  # fail open — allow the request

redis_client = RedisClient()

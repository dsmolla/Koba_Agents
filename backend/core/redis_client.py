from redis.asyncio import Redis

from config import Config
from core.token_encryption import token_encryptor


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
        token = await self.redis.get(f"{user_id}:{provider}")
        if not token:
            return None
        return token_encryptor.decrypt(token)

    async def set_provider_token(self, token: dict, user_id: str, provider: str) -> None:
        token = token_encryptor.encrypt(token)
        await self.redis.set(f"{user_id}:{provider}", token, ex=3600)

    async def delete_provider_token(self, user_id: str, provider: str) -> None:
        await self.redis.delete(f"{user_id}:{provider}")

redis_client = RedisClient()
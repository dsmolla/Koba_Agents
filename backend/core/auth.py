from google_client.api_service import APIServiceLayer
from langchain_core.runnables import RunnableConfig

from core.db import database
from core.exceptions import ProviderNotConnectedError
from core.redis_client import redis_client


async def get_google_service(user_id: str, timezone: str) -> APIServiceLayer:
    """Fetch Google API service layer from Redis/DB."""
    user_token = await redis_client.get_provider_token(user_id, 'google')
    if not user_token:
        user_token = await database.get_provider_token(user_id, 'google')
        if not user_token:
            raise ProviderNotConnectedError('Google')
        await redis_client.set_provider_token(user_id, 'google', user_token)

    return APIServiceLayer(user_token, timezone)


async def get_gmail_service(config: RunnableConfig):
    return config['configurable'].get('api_service').async_gmail

async def get_calendar_service(config: RunnableConfig):
    return config['configurable'].get('api_service').async_calendar


async def get_drive_service(config: RunnableConfig):
    return config['configurable'].get('api_service').async_drive


async def get_tasks_service(config: RunnableConfig):
    return config['configurable'].get('api_service').async_tasks

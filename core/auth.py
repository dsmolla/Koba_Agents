from asyncstdlib import lru_cache
from google_client.api_service import APIServiceLayer
from langchain_core.runnables import RunnableConfig
from core.db import db


@lru_cache(maxsize=100)
async def get_google_service(user_id: str, timezone: str):
    user_token = await db.get_provider_token(user_id, 'google')
    api_service = APIServiceLayer(user_token, timezone)
    return api_service

async def get_gmail_service(config: RunnableConfig):
    user_id = config['configurable'].get('thread_id')
    timezone = config['configurable'].get('timezone')
    api_service = await get_google_service(user_id, timezone)

    return api_service.async_gmail

async def get_calendar_service(config: RunnableConfig):
    user_id = config['configurable'].get('thread_id')
    timezone = config['configurable'].get('timezone')
    api_service = await get_google_service(user_id, timezone)

    return api_service.async_calendar

async def get_drive_service(config: RunnableConfig):
    user_id = config['configurable'].get('thread_id')
    timezone = config['configurable'].get('timezone')
    api_service = await get_google_service(user_id, timezone)

    return api_service.async_drive

async def get_tasks_service(config: RunnableConfig):
    user_id = config['configurable'].get('thread_id')
    timezone = config['configurable'].get('timezone')
    api_service = await get_google_service(user_id, timezone)
    
    return api_service.async_tasks

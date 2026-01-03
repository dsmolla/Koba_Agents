import json
from functools import lru_cache
from google_client.api_service import APIServiceLayer
from langchain_core.runnables import RunnableConfig


@lru_cache(maxsize=100)
def get_google_service(user_token: str, timezone: str):
    user_token = json.loads(user_token)
    api_service = APIServiceLayer(user_token, timezone)
    return api_service

def get_gmail_service(config: RunnableConfig):
    token = config['configurable'].get('google_token')
    timezone = config['configurable'].get('timezone')

    token = json.dumps(token)

    api_service = get_google_service(token, timezone)
    return api_service.async_gmail

def get_calendar_service(config: RunnableConfig):
    token = config['configurable'].get('google_token')
    timezone = config['configurable'].get('timezone')

    token = json.dumps(token)

    api_service = get_google_service(token, timezone)
    return api_service.async_calendar

def get_drive_service(config: RunnableConfig):
    token = config['configurable'].get('google_token')
    timezone = config['configurable'].get('timezone')

    token = json.dumps(token)

    api_service = get_google_service(token, timezone)
    return api_service.async_drive

def get_tasks_service(config: RunnableConfig):
    token = config['configurable'].get('google_token')
    timezone = config['configurable'].get('timezone')

    token = json.dumps(token)

    api_service = get_google_service(token, timezone)
    return api_service.async_tasks

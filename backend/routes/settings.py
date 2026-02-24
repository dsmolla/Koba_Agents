import logging
from typing import Any
from zoneinfo import available_timezones

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.db import database
from core.dependencies import get_current_user_http

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])

VALID_TIMEZONES = available_timezones()


class UserSettingsUpdate(BaseModel):
    timezone: str = Field(min_length=1, max_length=100)


@router.get("")
async def get_settings(user: Any = Depends(get_current_user_http)):
    timezone = await database.get_user_timezone(str(user.id))
    return {"timezone": timezone}


@router.put("")
async def update_settings(
        settings: UserSettingsUpdate,
        user: Any = Depends(get_current_user_http)
):
    if settings.timezone not in VALID_TIMEZONES:
        raise HTTPException(status_code=400, detail=f"Invalid timezone: {settings.timezone}")

    try:
        await database.set_user_timezone(str(user.id), settings.timezone)
        logger.info("User settings updated", extra={"user_id": user.id, "timezone": settings.timezone})
        return {"timezone": settings.timezone}
    except Exception as e:
        logger.error(f"Failed to update settings: {e}", extra={"user_id": user.id}, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update settings")

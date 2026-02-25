import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from core.dependencies import get_current_user_http
from core.redis_client import redis_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])


@router.post("/auth/ticket")
async def generate_ws_ticket(user: Any = Depends(get_current_user_http)):
    is_allowed, _ = await redis_client.check_rate_limit(
        f"ticket_gen:{user.id}", limit=5, window_seconds=60
    )
    if not is_allowed:
        raise HTTPException(status_code=429, detail="Too many requests")
    ticket = str(uuid.uuid4())
    await redis_client.set_ws_ticket(ticket, user.id)
    logger.debug("Generated WebSocket ticket", extra={"user_id": user.id})
    return {"ticket": ticket}

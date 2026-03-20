import logging
import secrets
from typing import Any

from fastapi import APIRouter, Request, HTTPException, Depends

from config import Config
from core.dependencies import verify_google_token
from services.auto_reply import process_notification

logger = logging.getLogger(__name__)

router = APIRouter(tags=["internal"])


@router.post("/internal/gmail/auto-reply/process")
async def process_auto_reply_task(
        request: Request,
        id_info: Any = Depends(verify_google_token(
            audience=Config.OIDC_AUDIENCE, 
            expected_email=Config.CLOUD_TASKS_SERVICE_ACCOUNT_EMAIL
        ))
):
    token = request.headers.get("X-Cloud-Tasks-Token")
    expected_token = Config.CLOUD_TASKS_TOKEN
    
    if not expected_token or not token or not secrets.compare_digest(token, expected_token):
        logger.warning("Invalid or missing Cloud Tasks token")
        raise HTTPException(status_code=403, detail="Forbidden")

    body = await request.json()
    user_id = body.get("user_id")
    history_id = body.get("history_id")

    logger.info("Processing Cloud Task", extra={"user_id": user_id, "history_id": history_id})

    await process_notification(user_id, int(history_id))

    return {"status": "ok"}

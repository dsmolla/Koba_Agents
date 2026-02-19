import base64
import json
import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Request, Query, HTTPException, Depends

from config import Config
from core.db import database
from core.dependencies import verify_google_token
from services.auto_reply import process_notification
from services.cloud_tasks import enqueue_notification_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/gmail")
async def gmail_push_notification(
        request: Request,
        background_tasks: BackgroundTasks,
        id_info: Any = Depends(verify_google_token),
        token: str | None = Query(default=None)
):
    if Config.PUBSUB_WEBHOOK_TOKEN and token != Config.PUBSUB_WEBHOOK_TOKEN:
        logger.warning("Invalid webhook token")
        raise HTTPException(status_code=403, detail="Forbidden")

    body = await request.json()
    message = body["message"]
    message_id = message["message_id"]
    data = message["data"]

    decoded = json.loads(base64.b64decode(data))
    email_address = decoded["emailAddress"]
    history_id = int(decoded["historyId"])

    if not email_address or not history_id:
        logger.warning("Missing emailAddress or historyId in notification")
        return {"status": "ok"}

    if await database.pubsub_notification_exists(message_id):
        logger.debug(f"Duplicate Pub/Sub message: {message_id}")
        return {"status": "ok"}

    await database.execute(
        "INSERT INTO public.pubsub_notifications (message_id, email, history_id) VALUES (%s, %s, %s)",
        (message_id, email_address, history_id)
    )

    watch_state = await database.fetch_one(
        "SELECT user_id FROM public.gmail_watch_state WHERE LOWER(email) = %s AND is_active = TRUE",
        (email_address,)
    )

    if not watch_state:
        logger.debug(f"No active watch state found for email: {email_address}")
        return {"status": "ok"}

    user_id = str(watch_state['user_id'])
    if Config.CLOUD_TASKS_PROJECT:
        await enqueue_notification_task(user_id, history_id)
    else:
        background_tasks.add_task(process_notification, user_id, history_id)

    logger.info(
        "Gmail notification dispatched",
        extra={"user_id": user_id, "email": email_address, "history_id": history_id}
    )

    return {"status": "ok"}

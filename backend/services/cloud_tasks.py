import json
import logging

from google.api_core.exceptions import AlreadyExists
from google.cloud import tasks_v2

from config import Config

logger = logging.getLogger(__name__)


async def enqueue_notification_task(user_id: str, history_id: int):
    client = tasks_v2.CloudTasksAsyncClient()
    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": f"{Config.BASE_PROJECT_URL}/internal/gmail/auto-reply/process",
            "oidc_token": {
                "service_account_email": Config.CLOUD_TASKS_SERVICE_ACCOUNT_EMAIL,
            },
            "headers": {
                "Content-Type": "application/json",
                "X-Cloud-Tasks-Token": Config.CLOUD_TASKS_TOKEN,
            },
            "body": json.dumps({"user_id": user_id, "history_id": history_id}).encode(),
        },
    }

    try:
        project = Config.CLOUD_TASKS_PROJECT
        location = Config.CLOUD_TASKS_LOCATION
        queue = Config.CLOUD_TASKS_QUEUE_NAME

        await client.create_task(request={"parent": client.queue_path(project, location, queue), "task": task})
        logger.debug("Cloud Task enqueued", extra={"user_id": user_id, "history_id": history_id})
    except AlreadyExists:
        logger.debug("Duplicate Cloud Task skipped", extra={"user_id": user_id, "history_id": history_id})
    except Exception as e:
        logger.error(f"Failed to enqueue Cloud Task: {e}", extra={"user_id": user_id}, exc_info=True)
        raise

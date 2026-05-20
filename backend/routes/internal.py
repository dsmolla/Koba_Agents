import logging
import secrets
from typing import Any

from fastapi import APIRouter, Request, HTTPException, Depends

from config import Config
from core.dependencies import verify_google_token
from services.auto_reply import process_notification
from core.db import database
from services.recursive_tasks import RecursiveTaskService
from services.cloud_tasks import enqueue_recursive_tasks_bulk


logger = logging.getLogger(__name__)

router = APIRouter(tags=["internal"])


@router.post("/internal/gmail/auto-reply/process")
async def process_auto_reply_task(
        request: Request,
        id_info: Any = Depends(verify_google_token(
            audience=Config.CLOUD_TASKS_GMAIL_WATCH_OIDC_AUDIENCE,
            expected_email=Config.CLOUD_TASKS_SERVICE_ACCOUNT_EMAIL
        ))
):
    token = request.headers.get("X-Cloud-Tasks-Token")
    expected_token = Config.CLOUD_TASKS_GMAIL_WATCH_TOKEN
    
    if not expected_token or not token or not secrets.compare_digest(token, expected_token):
        logger.warning("Invalid or missing Cloud Tasks token")
        raise HTTPException(status_code=403, detail="Forbidden")

    body = await request.json()
    user_id = body.get("user_id")
    history_id = body.get("history_id")

    logger.info("Processing Cloud Task", extra={"user_id": user_id, "history_id": history_id})

    await process_notification(user_id, int(history_id))

    return {"status": "ok"}


@router.post("/internal/tasks/process-due")
async def process_due_tasks(
        request: Request,
        id_info: Any = Depends(verify_google_token(
            audience=Config.CLOUD_SCHEDULER_RECURRING_TASKS_OIDC_AUDIENCE,
            expected_email=Config.CLOUD_TASKS_SERVICE_ACCOUNT_EMAIL
        ))
):
    token = request.headers.get("X-Cloud-Tasks-Token")
    expected_token = Config.CLOUD_SCHEDULER_RECURRING_TASKS_TOKEN

    if not expected_token or not token or not secrets.compare_digest(token, expected_token):
        logger.warning("Invalid or missing Cloud Tasks token")
        raise HTTPException(status_code=403, detail="Forbidden")

    logger.debug("Running serverless batch polling for due tasks")

    query = """
    UPDATE recursive_tasks
    SET next_run_at = NULL, last_run_at = NOW()
    WHERE id IN (
        SELECT id FROM recursive_tasks 
        WHERE status = 'active' AND next_run_at <= NOW()
        FOR UPDATE SKIP LOCKED
        LIMIT 500
    )
    RETURNING *;
    """
    records = await database.fetch_all(query)
    if not records:
        logger.debug("No due tasks found in this polling cycle")
        return {"status": "ok", "message": "No tasks due"}
        
    logger.debug(f"Fetched {len(records)} due tasks for processing")

    task_ids_to_enqueue = []

    update_params = []
    for task in records:
        task_id = str(task['id'])
        task_ids_to_enqueue.append(task_id)

        cron_schedule = task['cron_schedule']
        task_tz_str = task.get('timezone', 'UTC')
        next_run = RecursiveTaskService.calculate_next_run(cron_schedule, task_tz_str)
        update_params.append((next_run, task_id))

    if update_params:
        update_query = "UPDATE recursive_tasks SET next_run_at = %s WHERE id = %s"
        await database.execute_many(update_query, update_params)

    await enqueue_recursive_tasks_bulk(task_ids_to_enqueue)
    logger.debug(f"Successfully dispatched {len(records)} tasks to Cloud Tasks")

    return {"status": "ok", "processed": len(records)}

@router.post("/internal/tasks/execute/{task_id}")
async def execute_task(
        task_id: str,
        request: Request,
        id_info: Any = Depends(verify_google_token(
            audience=Config.CLOUD_TASKS_RECURRING_TASKS_OIDC_AUDIENCE,
            expected_email=Config.CLOUD_TASKS_SERVICE_ACCOUNT_EMAIL
        ))
):
    token = request.headers.get("X-Cloud-Tasks-Token")
    expected_token = Config.CLOUD_TASKS_RECURRING_TASKS_TOKEN
    if not expected_token or not token or not secrets.compare_digest(token, expected_token):
        logger.warning("Invalid or missing Cloud Tasks token")
        raise HTTPException(status_code=403, detail="Forbidden")

    query = "SELECT * FROM recursive_tasks WHERE id = %s"
    task = await database.fetch_one(query, (task_id,))
    if not task:
        logger.error(f"Task {task_id} not found for execution")
        return {"status": "not_found"}
        
    logger.debug(f"Executing cloud task worker for task_id: {task_id}")
        
    await RecursiveTaskService.execute_agent_for_task(dict(task), request.app)
    return {"status": "ok"}

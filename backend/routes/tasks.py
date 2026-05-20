from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Any
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage
from core.models import BotMessage
from config import Config

from core.db import database
import logging

from core.dependencies import get_current_user_http

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])

class TaskCreate(BaseModel):
    name: str
    cron_schedule: str
    human_schedule: str
    prompt: str

class TaskUpdate(BaseModel):
    status: Optional[str] = None
    name: Optional[str] = None
    cron_schedule: Optional[str] = None
    human_schedule: Optional[str] = None
    prompt: Optional[str] = None

from services.recursive_tasks import RecursiveTaskService

@router.get("")
async def list_tasks(user: Any = Depends(get_current_user_http)):
    logger.debug("Listing recursive tasks", extra={"user_id": str(user.id)})
    return await RecursiveTaskService.list_tasks(str(user.id))

@router.post("")
async def create_task(task: TaskCreate, user: Any = Depends(get_current_user_http)):
    logger.debug(f"Creating recursive task: {task.name} with schedule {task.cron_schedule}", extra={"user_id": str(user.id)})
    try:
        record = await RecursiveTaskService.create_task(
            user_id=str(user.id),
            name=task.name,
            cron_schedule=task.cron_schedule,
            human_schedule=task.human_schedule,
            prompt=task.prompt
        )
        return record
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{task_id}")
async def update_task(task_id: str, updates: TaskUpdate, user: Any = Depends(get_current_user_http)):
    logger.debug(f"Updating task {task_id}", extra={"user_id": str(user.id), "updates": updates.model_dump(exclude_unset=True)})
    try:
        updated_record = await RecursiveTaskService.update_task(
            task_id=task_id,
            user_id=str(user.id),
            **updates.model_dump(exclude_unset=True)
        )
        if not updated_record:
            raise HTTPException(status_code=404, detail="Task not found")
        return updated_record
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{task_id}")
async def delete_task(task_id: str, user: Any = Depends(get_current_user_http)):
    logger.debug(f"Deleting task {task_id}", extra={"user_id": str(user.id)})
    deleted = await RecursiveTaskService.delete_task(task_id, str(user.id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "deleted"}

@router.get("/{task_id}/logs")
async def get_task_logs(task_id: str, user: Any = Depends(get_current_user_http)):
    logger.debug(f"Fetching logs for task {task_id}", extra={"user_id": str(user.id)})
    query = "SELECT id FROM recursive_tasks WHERE id = %s AND user_id = %s"
    task = await database.fetch_one(query, (task_id, user.id))
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    query_logs = "SELECT * FROM recursive_task_logs WHERE task_id = %s ORDER BY executed_at DESC LIMIT 50"
    logs = await database.fetch_all(query_logs, (task_id,))
    return [dict(log) for log in logs]

@router.post("/{task_id}/run")
async def run_task(task_id: str, request: Request, user: Any = Depends(get_current_user_http)):
    logger.debug(f"Manual run triggered for task {task_id}", extra={"user_id": str(user.id)})
    query = "SELECT * FROM recursive_tasks WHERE id = %s AND user_id = %s"
    task = await database.fetch_one(query, (task_id, user.id))
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    await database.execute("UPDATE recursive_tasks SET last_run_at = NOW() WHERE id = %s", (task_id,))
    
    from services.cloud_tasks import enqueue_recursive_tasks_bulk
    await enqueue_recursive_tasks_bulk([task_id])
    
    return {"status": "started"}

@router.get("/{thread_id}")
async def get_task_history(thread_id: str, request: Request, user: Any = Depends(get_current_user_http)):
    if thread_id != str(user.id):
        query = "SELECT id FROM recursive_task_logs WHERE thread_id = %s AND user_id = %s"
        log = await database.fetch_one(query, (thread_id, user.id))
        if not log:
            raise HTTPException(status_code=403, detail="Access denied")

    config = RunnableConfig(configurable={"thread_id": thread_id})
    from main import get_agent
    agent = get_agent(request.app, Config.DEFAULT_MODEL)
    
    try:
        state_snapshot = await agent.agent.aget_state(config)
        messages = state_snapshot.values.get("messages", [])[-200:]
        history_payload = []
        for msg in messages:
            if isinstance(msg, HumanMessage) and msg.name in ["RealUser", "RecursiveSystemCall"]:
                content = msg.content
                history_payload.append({
                    "sender": "user",
                    "content": content,
                    "timestamp": msg.additional_kwargs.get("timestamp", "")
                })
            elif isinstance(msg, AIMessage) and msg.name == "SupervisorAgent":
                if msg.tool_calls and msg.tool_calls[0]['name'] == 'BotMessage':
                    args = msg.tool_calls[0]['args']
                    history_payload.append(
                        BotMessage(
                            content=args.get('content', ''),
                            files=args.get('files', []),
                        ).model_dump()
                    )
        return {"messages": history_payload}
    except Exception as e:
        logger.error(f"Failed to fetch history for thread {thread_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch history")

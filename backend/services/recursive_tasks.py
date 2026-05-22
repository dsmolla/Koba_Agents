from config import Config
import logging
from datetime import datetime
import zoneinfo
import croniter
from typing import List, Dict, Optional, Any

from core.db import database

logger = logging.getLogger(__name__)

class RecursiveTaskService:
    @staticmethod
    async def list_tasks(user_id: str) -> List[Dict]:
        query = "SELECT * FROM recursive_tasks WHERE user_id = %s ORDER BY created_at DESC"
        records = await database.fetch_all(query, (user_id,))
        return [dict(r) for r in records]

    @staticmethod
    async def get_task(task_id: str, user_id: str) -> Optional[Dict]:
        query = "SELECT * FROM recursive_tasks WHERE id = %s AND user_id = %s"
        record = await database.fetch_one(query, (task_id, user_id))
        return dict(record) if record else None

    @staticmethod
    def calculate_next_run(cron_schedule: str, timezone_str: str = 'UTC') -> datetime:
        if not croniter.croniter.is_valid(cron_schedule):
            raise ValueError(f"Invalid CRON schedule: {cron_schedule}")
            
        tz = zoneinfo.ZoneInfo(timezone_str)
        now = datetime.now(tz)
        iter_obj = croniter.croniter(cron_schedule, now)
        
        first_run = iter_obj.get_next(datetime)
        second_run = iter_obj.get_next(datetime)
        
        interval_seconds = (second_run - first_run).total_seconds()
        
        if interval_seconds < Config.MIN_RECURSIVE_TASK_INTERVAL_SECONDS:
            logger.warning(f"Rejected CRON schedule due to interval check: {interval_seconds}s")
            raise ValueError(f"Schedule is too frequent. Minimum allowed interval is {Config.MIN_RECURSIVE_TASK_INTERVAL_SECONDS // 60} minutes.")
            
        next_run = first_run.replace(tzinfo=tz)
        logger.debug(f"Calculated next run: {next_run} (interval: {interval_seconds}s)")
        return next_run.astimezone(zoneinfo.ZoneInfo("UTC"))

    @staticmethod
    async def create_task(user_id: str, name: str, cron_schedule: str, human_schedule: str, prompt: str) -> Dict:
        if not croniter.croniter.is_valid(cron_schedule):
            raise ValueError(f"Invalid CRON schedule: {cron_schedule}")

        user_tz_str = await database.get_user_timezone(user_id)
        next_run = RecursiveTaskService.calculate_next_run(cron_schedule, user_tz_str)

        query = """
        INSERT INTO recursive_tasks (user_id, name, cron_schedule, human_schedule, prompt, next_run_at, timezone)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING *;
        """
        record = await database.fetch_one(query, (
            user_id,
            name,
            cron_schedule,
            human_schedule,
            prompt,
            next_run,
            user_tz_str
        ))
        return dict(record)

    @staticmethod
    async def update_task(task_id: str, user_id: str, **updates) -> Optional[Dict]:
        task = await RecursiveTaskService.get_task(task_id, user_id)
        if not task:
            return None

        if not updates:
            return task

        update_fields = []
        values = tuple()
        for k, v in updates.items():
            if v is not None:
                update_fields.append(f"{k} = %s")
                values = values + (v, )
            
        if "cron_schedule" in updates and updates["cron_schedule"] is not None:
            cron = updates["cron_schedule"]
            task_tz_str = task.get("timezone", "UTC")
            next_run = RecursiveTaskService.calculate_next_run(cron, task_tz_str)
            
            update_fields.append("next_run_at = %s")
            values = values + (next_run, )

        if not update_fields:
            return task

        update_fields.append("updated_at = NOW()")
        update_query = f"UPDATE recursive_tasks SET {', '.join(update_fields)} WHERE id = %s AND user_id = %s RETURNING *"
        updated_record = await database.fetch_one(update_query, values + (task_id, user_id))
        
        return dict(updated_record) if updated_record else None

    @staticmethod
    async def delete_task(task_id: str, user_id: str) -> bool:
        query = "DELETE FROM recursive_tasks WHERE id = %s AND user_id = %s RETURNING id"
        deleted = await database.fetch_one(query, (task_id, user_id))
        return bool(deleted)

    @staticmethod
    async def execute_agent_for_task(task: Dict, app: Any):
        import uuid
        from config import Config
        from langchain_core.messages import SystemMessage, HumanMessage
        from core.auth import get_google_service
        from main import get_agent
        from core.models import BotMessage

        task_id = str(task['id'])
        user_id = str(task['user_id'])
        prompt = task['prompt']
        timezone = task.get('timezone', 'UTC')
        
        task_execution_uuid = uuid.uuid4().hex[:8]
        thread_id = f"recursive_task_{task_id}_{task_execution_uuid}"
        
        mem_chunk = await app.state.store.asearch(("memory", user_id))
        session_memories = ""
        if mem_chunk:
            facts = [f"MEMORY_ID: `{mem.key}` | CATEGORY: {mem.value.get('category')} | FACT: {mem.value.get('fact')}"
                     for mem in mem_chunk if mem.value.get("fact")]
            if facts:
                session_memories = "CRITICAL INSTRUCTION: The following are the user's existing saved memories/preferences. " \
                                   "DO NOT call create_memory to create a new fact if one already exists. " \
                                   "If a preference changes, you MUST update the existing one by passing its EXACT MEMORY_ID to the update_memory tool. " \
                                   "If it is no longer relevant, pass the MEMORY_ID to the delete_memory tool.\n" + "\n".join(facts)

        config = {"configurable": {
            "thread_id": thread_id,
            "user_id": user_id,
            "timezone": timezone,
            "api_service": await get_google_service(user_id, timezone),
        }}

        logger.debug(f"Initializing AI agent for recursive task {task_id}", extra={"user_id": user_id, "thread_id": thread_id})
        agent = get_agent(app, Config.DEFAULT_MODEL)

        messages = {
            'messages': [
                SystemMessage(content=session_memories),
                HumanMessage(content=prompt),
            ]
        }
        
        logger.debug(f"Injecting prompt into LangGraph for task {task_id}: {prompt}", extra={"user_id": user_id})

        try:
            final_output = await agent.agent.ainvoke(messages, config)
            structured_output: BotMessage = final_output['structured_response']
            text_content = structured_output.content
            logger.debug(f"Agent execution completed successfully for task {task_id}", extra={"user_id": user_id, "output_snippet": text_content[:100]})
            status = "success"
        except Exception as e:
            logger.error(f"Execution failed for task {task_id}: {e}")
            text_content = f"Error: {str(e)}"
            status = "failed"
            # We must remember to raise this at the end so Cloud Tasks retries it
            agent_exception = e
        else:
            agent_exception = None
            
        log_query = """
        INSERT INTO recursive_task_logs (task_id, user_id, status, output, thread_id)
        VALUES (%s, %s, %s, %s, %s)
        """
        await database.execute(log_query, (
            task_id,
            user_id,
            status,
            (text_content[:150] + "...") if text_content and len(text_content) > 150 else (text_content if text_content else "Finished successfully."),
            thread_id
        ))

        if agent_exception:
            raise agent_exception

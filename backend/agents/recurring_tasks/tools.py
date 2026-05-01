import logging
from typing import Optional, Annotated
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool, InjectedToolArg
from langchain_core.runnables import RunnableConfig

from services.recursive_tasks import RecursiveTaskService

logger = logging.getLogger(__name__)

class CreateRecursiveTaskInput(BaseModel):
    name: str = Field(..., description="Short descriptive name for the task, e.g., 'Daily News Summary'")
    cron_schedule: str = Field(..., description="Valid standard CRON expression, e.g., '0 9 * * *' for every day at 9am. Format is MIN HOUR DAY MONTH DAY_OF_WEEK.")
    human_schedule: str = Field(..., description="A natural language description of the schedule, e.g., 'Every day at 9:00 AM'")
    prompt: str = Field(..., description="The highly specific prompt instruction that will execute autonomously when the task runs.")

class CreateRecursiveTaskTool(BaseTool):
    name: str = "create_recursive_task"
    description: str = "Use this to create a new recursive / scheduled background task. It requires a proper cron expression."
    args_schema: type[BaseModel] = CreateRecursiveTaskInput

    def _run(self, name: str, cron_schedule: str, human_schedule: str, prompt: str) -> str:
        raise NotImplementedError("This tool requires async execution.")

    async def _arun(self, name: str, cron_schedule: str, human_schedule: str, prompt: str, config: Annotated[RunnableConfig, InjectedToolArg] = None) -> str:
        try:
            user_id = config.get("configurable", {}).get("user_id")
            if not user_id:
                return "Error: User ID not found in context."

            record = await RecursiveTaskService.create_task(
                user_id=user_id,
                name=name,
                cron_schedule=cron_schedule,
                human_schedule=human_schedule,
                prompt=prompt
            )
            return f"Successfully created recursive task '{name}'. ID: {record['id']}. It will first run at {record['next_run_at']} UTC."
        except ValueError as ve:
            return f"Error creating task: {str(ve)}"
        except Exception as e:
            logger.error(f"Error creating recursive task: {e}")
            return f"Error creating task: {str(e)}"

class DeleteRecursiveTaskInput(BaseModel):
    task_id: str = Field(..., description="The UUID of the task to delete")

class DeleteRecursiveTaskTool(BaseTool):
    name: str = "delete_recursive_task"
    description: str = "Deletes a specific recursive task by its ID."
    args_schema: type[BaseModel] = DeleteRecursiveTaskInput

    def _run(self, task_id: str) -> str:
        raise NotImplementedError("This tool requires async execution.")

    async def _arun(self, task_id: str, config: Annotated[RunnableConfig, InjectedToolArg] = None) -> str:
        try:
            user_id = config.get("configurable", {}).get("user_id")
            if not user_id:
                return "Error: User ID not found."

            deleted = await RecursiveTaskService.delete_task(task_id, user_id)
            if not deleted:
                return f"Warning: Task {task_id} not found."
            return f"Successfully deleted Task {task_id}."
        except Exception as e:
            return f"Error deleting task: {str(e)}"

class ListRecursiveTasksTool(BaseTool):
    name: str = "list_recursive_tasks"
    description: str = "Use this to see all currently active or paused recursive tasks."

    def _run(self) -> str:
        raise NotImplementedError("Requires async")

    async def _arun(self, config: Annotated[RunnableConfig, InjectedToolArg] = None) -> str:
        try:
            user_id = config.get("configurable", {}).get("user_id")
            if not user_id:
                return "Error: User ID not found."

            records = await RecursiveTaskService.list_tasks(user_id)
            if not records:
                return "No recursive tasks found."
            
            output = "Here are your recursive tasks:\n"
            for row in records:
                output += f"- ID: {row['id']} | Name: {row['name']} | Schedule: {row['human_schedule']} | Status: {row['status']} | Prompt: {row['prompt']}\n"
            return output
        except Exception as e:
            return f"Error listing tasks: {str(e)}"

class UpdateRecursiveTaskInput(BaseModel):
    task_id: str = Field(..., description="The UUID of the task to update")
    name: Optional[str] = Field(None, description="New name")
    cron_schedule: Optional[str] = Field(None, description="New valid standard CRON expression")
    human_schedule: Optional[str] = Field(None, description="New natural language description")
    prompt: Optional[str] = Field(None, description="New execution prompt")
    status: Optional[str] = Field(None, description="New status ('active' or 'paused')")

class UpdateRecursiveTaskTool(BaseTool):
    name: str = "update_recursive_task"
    description: str = "Updates an existing recursive task. Provide only the fields you wish to change. IMPORTANT: If updating the schedule, you MUST provide BOTH 'cron_schedule' AND 'human_schedule'."
    args_schema: type[BaseModel] = UpdateRecursiveTaskInput

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("This tool requires async execution.")

    async def _arun(self, task_id: str, config: Annotated[RunnableConfig, InjectedToolArg] = None, **kwargs) -> str:
        try:
            user_id = config.get("configurable", {}).get("user_id")
            if not user_id:
                return "Error: User ID not found."

            # Exclude None values that aren't provided
            updates = {k: v for k, v in kwargs.items() if v is not None}
            if not updates:
                return "No updates provided."

            updated = await RecursiveTaskService.update_task(task_id, user_id, **updates)
            if not updated:
                return f"Warning: Task {task_id} not found."
                
            return f"Successfully updated Task {task_id}."
        except ValueError as ve:
            return f"Error: {str(ve)}"
        except Exception as e:
            logger.error(f"Error updating task: {e}")
            return f"Error updating task: {str(e)}"

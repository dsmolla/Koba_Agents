import json
import logging
from datetime import datetime
from typing import Optional, Literal, Union, Annotated

from langchain_core.callbacks import adispatch_custom_event
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import ArgsSchema, InjectedToolArg
from pydantic import BaseModel, Field

from agents.common.tools import BaseGoogleTool
from core.auth import get_tasks_service
from google_client.services.tasks import TaskQueryBuilder
from google_client.services.tasks.async_query_builder import AsyncTaskQueryBuilder

logger = logging.getLogger(__name__)


class CreateTaskInput(BaseModel):
    title: str = Field(description="The title of the task to create")
    notes: Optional[str] = Field(default=None, description="The notes/details of the task")
    due: Optional[str] = Field(default=None, description="The due date of the task in YYYY-mm-dd format")
    task_list_id: Optional[str] = Field(default='@default',
                                        description="The task_list_id to add the task to, defaults to '@default'")


class CreateTaskTool(BaseGoogleTool):
    name: str = "create_task"
    description: str = "Create a new task"
    args_schema: ArgsSchema = CreateTaskInput

    def _run(
            self,
            title: str,
            config: Annotated[RunnableConfig, InjectedToolArg],
            notes: Optional[str] = None,
            due: Optional[str] = None,
            task_list_id: str = "@default",
    ) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(
            self,
            config: RunnableConfig,
            title: str,
            notes: Optional[str] = None,
            due: Optional[str] = None,
            task_list_id: str = "@default",
    ) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Creating Task...", "icon": "✅"}
        )
        tasks_service = await get_tasks_service(config)
        due = datetime.strptime(due, "%Y-%m-%d") if due else None
        task = await tasks_service.create_task(
            title=title,
            notes=notes,
            due=due,
            task_list_id=task_list_id
        )
        return f"Task '{task.title}' created successfully. task_id: {task.task_id}, task_list_id: {task.task_list_id}"


class ListTasksInput(BaseModel):
    task_list_id: Optional[str] = Field(default='@default',
                                        description="The task_list_id to list tasks from, defaults to '@default'")
    max_results: Optional[int] = Field(default=10, description="The maximum number of tasks to return")
    show_completed: Optional[bool] = Field(default=False, description="Whether to include completed tasks")
    due_before: Optional[str] = Field(default=None,
                                      description="Return tasks due before this date (exclusive) (YYYY-mm-dd)")
    due_after: Optional[str] = Field(default=None, description="Return tasks due after this date (YYYY-mm-dd)")
    date_filter: Optional[Literal["TODAY", "TOMORROW", "THIS_WEEK", "NEXT_WEEK"]] = (
        Field(None, description=("Predefined date filters to filter events. "
                                 "Overrides datetime_min and datetime_max if provided. "
                                 "Options are: TODAY, TOMORROW, THIS_WEEK, NEXT_WEEK"
                                 )
              )
    )


class ListTasksTool(BaseGoogleTool):
    name: str = "list_tasks"
    description: str = "List tasks"
    args_schema: ArgsSchema = ListTasksInput

    def _run(
            self,
            config: Annotated[RunnableConfig, InjectedToolArg],
            task_list_id: str = "@default",
            max_results: int = 20,
            show_completed: bool = False,
            due_before: Optional[str] = None,
            due_after: Optional[str] = None,
            date_filter: Optional[Literal["TODAY", "TOMORROW", "THIS_WEEK", "NEXT_WEEK"]] = None,
    ) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(
            self,
            config: RunnableConfig,
            task_list_id: str = "@default",
            max_results: int = 20,
            show_completed: bool = False,
            due_before: Optional[str] = None,
            due_after: Optional[str] = None,
            date_filter: Optional[Literal["TODAY", "TOMORROW", "THIS_WEEK", "NEXT_WEEK"]] = None,
    ) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Listing Tasks...", "icon": "📋"}
        )
        tasks_service = await get_tasks_service(config)
        params = {
            "task_list_id": task_list_id,
            "max_results": max_results,
            "show_completed": show_completed,
            "due_before": due_before,
            "due_after": due_after,
            "date_filter": date_filter,
        }
        builder = self.query_builder(tasks_service, params)
        tasks = await builder.execute()

        tasks_data = []
        for task in tasks:
            tasks_data.append(
                {
                    "task_id": task.task_id,
                    "task_list_id": task.task_list_id,
                    "title": task.title,
                    "notes": task.notes,
                    "due": task.due.strftime("%a, %B %d, %Y") if task.due else None,
                    "status": task.status,
                }
            )

        return json.dumps(tasks_data)

    def query_builder(self, service, params: dict) -> Union[TaskQueryBuilder, AsyncTaskQueryBuilder]:
        builder = service.query()
        if params.get('task_list_id'):
            builder = builder.in_task_list(params['task_list_id'])
        if params.get('max_results'):
            builder = builder.limit(params['max_results'])
        if params.get('show_completed'):
            builder = builder.show_completed()
        if params.get('due_before'):
            due_before_dt = datetime.strptime(params['due_before'], "%Y-%m-%d")
            builder = builder.due_before(due_before_dt)
        if params.get('due_after'):
            due_after_dt = datetime.strptime(params['due_after'], "%Y-%m-%d")
            builder = builder.due_after(due_after_dt)
        if params.get("date_filter"):
            match params["date_filter"]:
                case "TODAY":
                    builder = builder.due_today()
                case "TOMORROW":
                    builder = builder.due_tomorrow()
                case "THIS_WEEK":
                    builder = builder.due_this_week()
                case "NEXT_WEEK":
                    builder = builder.due_next_week()
        return builder


class DeleteTaskInput(BaseModel):
    task_id: str = Field(description="The ID of the task to delete")
    task_list_id: Optional[str] = Field(default='@default',
                                        description="The task_list_id the task belongs to, defaults to '@default'")


class DeleteTaskTool(BaseGoogleTool):
    name: str = "delete_task"
    description: str = "Delete a task"
    args_schema: ArgsSchema = DeleteTaskInput

    def _run(self, task_id: str, config: Annotated[RunnableConfig, InjectedToolArg],
             task_list_id: str = "@default") -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, task_id: str,
                    task_list_id: str = "@default") -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Deleting Task...", "icon": "🗑️"}
        )
        tasks_service = await get_tasks_service(config)
        await tasks_service.delete_task(task=task_id, task_list_id=task_list_id)
        return f"Task deleted successfully. task_id: {task_id}, task_list_id: {task_list_id}"


class CompleteTaskInput(BaseModel):
    task_id: str = Field(description="The ID of the task to complete")
    task_list_id: Optional[str] = Field(default='@default',
                                        description="The task list ID the task belongs to, defaults to '@default'")


class CompleteTaskTool(BaseGoogleTool):
    name: str = "complete_task"
    description: str = "Mark a task as completed"
    args_schema: ArgsSchema = CompleteTaskInput

    def _run(self, task_id: str, config: Annotated[RunnableConfig, InjectedToolArg],
             task_list_id: str = "@default") -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, task_id: str,
                    task_list_id: str = "@default") -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Completing Task...", "icon": "✅"}
        )
        tasks_service = await get_tasks_service(config)
        task = await tasks_service.mark_completed(task=task_id, task_list_id=task_list_id)
        return f"Task marked as completed. task_id: {task.task_id}, task_list_id: {task.task_list_id}"


class ReopenTaskInput(BaseModel):
    task_id: str = Field(description="The ID of the task to reopen")
    task_list_id: Optional[str] = Field(default='@default',
                                        description="The task list ID the task belongs to, defaults to '@default'")


class ReopenTaskTool(BaseGoogleTool):
    name: str = "reopen_task"
    description: str = "Reopen a completed task"
    args_schema: ArgsSchema = ReopenTaskInput

    def _run(self, task_id: str, config: Annotated[RunnableConfig, InjectedToolArg],
             task_list_id: str = "@default") -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, task_id: str,
                    task_list_id: str = "@default") -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Reopening Task...", "icon": "🔄"}
        )
        tasks_service = await get_tasks_service(config)
        task = await tasks_service.mark_incomplete(task=task_id, task_list_id=task_list_id)
        return f"Task reopened successfully. task_id: {task.task_id}, task_list_id: {task.task_list_id}"


class UpdateTaskInput(BaseModel):
    task_id: str = Field(description="The ID of the task to update")
    title: Optional[str] = Field(default=None, description="The new title of the task")
    notes: Optional[str] = Field(default=None, description="The new notes/details of the task")
    due: Optional[str] = Field(default=None, description="The new due date of the task in YYYY-mm-dd format")
    task_list_id: Optional[str] = Field(default='@default',
                                        description="The task list ID the task belongs to, defaults to '@default'")


class UpdateTaskTool(BaseGoogleTool):
    name: str = "update_task"
    description: str = "Update a task"
    args_schema: ArgsSchema = UpdateTaskInput

    def _run(
            self,
            task_id: str,
            config: Annotated[RunnableConfig, InjectedToolArg],
            title: Optional[str] = None,
            notes: Optional[str] = None,
            due: Optional[str] = None,
            task_list_id: str = "@default",
    ) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(
            self,
            config: RunnableConfig,
            task_id: str,
            title: Optional[str] = None,
            notes: Optional[str] = None,
            due: Optional[str] = None,
            task_list_id: str = "@default",
    ) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Updating Task...", "icon": "✏️"}
        )
        tasks_service = await get_tasks_service(config)
        task = await tasks_service.get_task(task_id=task_id, task_list_id=task_list_id)
        if title is not None:
            task.title = title
        if notes is not None:
            task.notes = notes
        if due is not None:
            task.due = datetime.strptime(due, "%Y-%m-%d").date()

        updated_task = await tasks_service.update_task(task=task, task_list_id=task_list_id)
        return f"Task updated successfully. task_id: {updated_task.task_id}, task_list_id: {updated_task.task_list_id}"


class CreateTaskListInput(BaseModel):
    title: str = Field(description="The title of the task list to create")


class CreateTaskListTool(BaseGoogleTool):
    name: str = "create_task_list"
    description: str = "Create a new task list"
    args_schema: ArgsSchema = CreateTaskListInput

    def _run(self, title: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, title: str) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Creating Task List...", "icon": "📝"}
        )
        tasks_service = await get_tasks_service(config)
        task_list = await tasks_service.create_task_list(title=title)
        return f"Task List created successfully. task_list_id: {task_list.task_list_id}"


class ListTaskListsTool(BaseGoogleTool):
    name: str = "list_task_lists"
    description: str = "List task lists"

    def _run(self, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Listing Task Lists...", "icon": "📋"}
        )
        tasks_service = await get_tasks_service(config)
        task_lists = await tasks_service.list_task_lists()
        return json.dumps(task_lists)
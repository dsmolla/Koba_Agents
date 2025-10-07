import json
from datetime import datetime
from typing import Optional, Literal

from google_client.services.tasks import TaskQueryBuilder
from google_client.services.tasks.api_service import TasksApiService
from langchain.tools.base import BaseTool
from langchain_core.tools import ArgsSchema
from pydantic import BaseModel, Field

from agents.tasks.task_list_cache import TaskListCache
from shared.exceptions import ToolException
from shared.response import ToolResponse


class CreateTaskInput(BaseModel):
    title: str = Field(description="The title of the task to create")
    notes: Optional[str] = Field(default=None, description="The notes/details of the task")
    due: Optional[str] = Field(default=None, description="The due date of the task in YYYY-mm-dd format")
    task_list_id: Optional[str] = Field(default='@default',
                                        description="The task_list_id to add the task to, defaults to '@default'")


class CreateTaskTool(BaseTool):
    name: str = "create_task"
    description: str = "Create a new task"
    args_schema: ArgsSchema = CreateTaskInput

    tasks_service: TasksApiService

    def __init__(self, tasks_service: TasksApiService):
        super().__init__(tasks_service=tasks_service)

    def _run(
            self,
            title: str,
            notes: Optional[str] = None,
            due: Optional[str] = None,
            task_list_id: str = "@default",
    ) -> ToolResponse:
        try:
            due = datetime.strptime(due, "%Y-%m-%d") if due else None
            task = self.tasks_service.create_task(
                title=title,
                notes=notes,
                due=due,
                task_list_id=task_list_id
            )
            return ToolResponse(
                status="success",
                message=f"Task '{task.title}' created successfully. task_id: {task.task_id}, task_list_id: {task.task_list_id}",
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to create task: {str(e)}"
            )


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


class ListTasksTool(BaseTool):
    name: str = "list_tasks"
    description: str = "List tasks"
    args_schema: ArgsSchema = ListTasksInput

    tasks_service: TasksApiService

    def __init__(self, tasks_service: TasksApiService):
        super().__init__(tasks_service=tasks_service)

    def _run(
            self,
            task_list_id: str = "@default",
            max_results: int = 20,
            show_completed: bool = False,
            due_before: Optional[str] = None,
            due_after: Optional[str] = datetime.today().strftime("%Y-%m-%d"),
            date_filter: Optional[Literal["TODAY", "TOMORROW", "THIS_WEEK", "NEXT_WEEK"]] = None,
    ) -> ToolResponse:
        try:
            params = {
                "task_list_id": task_list_id,
                "max_results": max_results,
                "show_completed": show_completed,
                "due_before": due_before,
                "due_after": due_after,
                "date_filter": date_filter,
            }
            builder = self.query_builder(params)
            tasks = builder.execute()

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

            return ToolResponse(
                status="success",
                message=json.dumps(tasks_data),
            )
        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to list tasks: {str(e)}"
            )

    def query_builder(self, params: dict) -> TaskQueryBuilder:
        builder = self.tasks_service.query()
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


class DeleteTaskTool(BaseTool):
    name: str = "delete_task"
    description: str = "Delete a task"
    args_schema: ArgsSchema = DeleteTaskInput

    tasks_service: TasksApiService

    def __init__(self, tasks_service: TasksApiService):
        super().__init__(tasks_service=tasks_service)

    def _run(self, task_id: str, task_list_id: str = "@default") -> ToolResponse:
        try:
            self.tasks_service.delete_task(task=task_id, task_list_id=task_list_id)
            return ToolResponse(
                status="success",
                message=f"Task deleted successfully. task_id: {task_id}, task_list_id: {task_list_id}"
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to delete task: {str(e)}"
            )


class CompleteTaskInput(BaseModel):
    task_id: str = Field(description="The ID of the task to complete")
    task_list_id: Optional[str] = Field(default='@default',
                                        description="The task list ID the task belongs to, defaults to '@default'")


class CompleteTaskTool(BaseTool):
    name: str = "complete_task"
    description: str = "Mark a task as completed"
    args_schema: ArgsSchema = CompleteTaskInput

    tasks_service: TasksApiService

    def __init__(self, tasks_service: TasksApiService):
        super().__init__(tasks_service=tasks_service)

    def _run(self, task_id: str, task_list_id: str = "@default") -> ToolResponse:
        try:
            task = self.tasks_service.mark_completed(task=task_id, task_list_id=task_list_id)
            return ToolResponse(
                status="success",
                message=f"Task marked as completed. task_id: {task.task_id}, task_list_id: {task.task_list_id}"
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to complete task: {str(e)}"
            )


class ReopenTaskInput(BaseModel):
    task_id: str = Field(description="The ID of the task to reopen")
    task_list_id: Optional[str] = Field(default='@default',
                                        description="The task list ID the task belongs to, defaults to '@default'")


class ReopenTaskTool(BaseTool):
    name: str = "reopen_task"
    description: str = "Reopen a completed task"
    args_schema: ArgsSchema = ReopenTaskInput

    tasks_service: TasksApiService

    def __init__(self, tasks_service: TasksApiService):
        super().__init__(tasks_service=tasks_service)

    def _run(self, task_id: str, task_list_id: str = "@default") -> ToolResponse:
        try:
            task = self.tasks_service.mark_incomplete(task=task_id, task_list_id=task_list_id)
            return ToolResponse(
                status="success",
                message=f"Task reopened successfully. task_id: {task.task_id}, task_list_id: {task.task_list_id}"
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to reopen task: {str(e)}"
            )


class UpdateTaskInput(BaseModel):
    task_id: str = Field(description="The ID of the task to update")
    title: Optional[str] = Field(default=None, description="The new title of the task")
    notes: Optional[str] = Field(default=None, description="The new notes/details of the task")
    due: Optional[str] = Field(default=None, description="The new due date of the task in YYYY-mm-dd format")
    task_list_id: Optional[str] = Field(default='@default',
                                        description="The task list ID the task belongs to, defaults to '@default'")


class UpdateTaskTool(BaseTool):
    name: str = "update_task"
    description: str = "Update a task"
    args_schema: ArgsSchema = UpdateTaskInput

    tasks_service: TasksApiService

    def __init__(self, tasks_service: TasksApiService):
        super().__init__(tasks_service=tasks_service)

    def _run(
            self,
            task_id: str,
            title: Optional[str] = None,
            notes: Optional[str] = None,
            due: Optional[str] = None,
            task_list_id: str = "@default",
    ) -> ToolResponse:
        try:
            task = self.tasks_service.get_task(task_id=task_id, task_list_id=task_list_id)
            if title is not None:
                task.title = title
            if notes is not None:
                task.notes = notes
            if due is not None:
                task.due = datetime.strptime(due, "%Y-%m-%d").date()

            updated_task = self.tasks_service.update_task(task=task, task_list_id=task_list_id)
            return ToolResponse(
                status="success",
                message=f"Task updated successfully. task_id: {updated_task.task_id}, task_list_id: {updated_task.task_list_id}",
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to update task: {str(e)}"
            )


class CreateTaskListInput(BaseModel):
    title: str = Field(description="The title of the task list to create")


class CreateTaskListTool(BaseTool):
    name: str = "create_task_list"
    description: str = "Create a new task list"
    args_schema: ArgsSchema = CreateTaskListInput

    tasks_service: TasksApiService
    task_list_cache: TaskListCache

    def __init__(self, tasks_service: TasksApiService, task_list_cache: TaskListCache):
        super().__init__(tasks_service=tasks_service, task_list_cache=task_list_cache)

    def _run(self, title: str) -> ToolResponse:
        try:
            task_list = self.tasks_service.create_task_list(title=title)
            self.task_list_cache.add_task_list(task_list)
            return ToolResponse(
                status="success",
                message=f"Task List created successfully. task_list_id: {task_list.task_list_id}"
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to create task list: {str(e)}"
            )


class ListTaskListsTool(BaseTool):
    name: str = "list_task_lists"
    description: str = "List task lists"

    tasks_service: TasksApiService
    task_list_cache: TaskListCache

    def __init__(self, tasks_service: TasksApiService, task_list_cache: TaskListCache):
        super().__init__(tasks_service=tasks_service, task_list_cache=task_list_cache)

    def _run(self) -> ToolResponse:
        try:
            task_lists = self.task_list_cache.list_task_lists()
            if len(task_lists) == 0:
                task_lists = self.tasks_service.list_task_lists()
                self.task_list_cache.update_cache(task_lists)
                task_lists = self.task_list_cache.list_task_lists()

            return ToolResponse(
                status="success",
                message=json.dumps(task_lists),
            )
        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to list task lists: {str(e)}"
            )

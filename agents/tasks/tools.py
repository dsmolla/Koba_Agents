from google_client.services.tasks import TaskQueryBuilder
from langchain.tools import BaseTool
from google_client.services.tasks.api_service import TasksApiService
from typing import Optional, Union

from langchain_core.tools import ArgsSchema
from pydantic import BaseModel, Field
from datetime import datetime


def query_builder(tasks_service: TasksApiService, params: dict) -> TaskQueryBuilder:
    """Helper function to build a TaskQueryBuilder from params"""
    builder = tasks_service.query()
    if params.get('tasklist'):
        builder = builder.in_task_list(params['tasklist'])
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
    return builder


class CreateTaskInput(BaseModel):
    """Input schema for getting creating a new task"""
    title: str = Field(description="The title of the task to create")
    notes: Optional[str] = Field(default=None, description="The notes/details of the task")
    due: Optional[str] = Field(default=None, description="The due date of the task in YYYY-mm-dd format")
    tasklist: Optional[str] = Field(default='@default', description="The task list ID to add the task to, defaults to '@default'")


class CreateTaskTool(BaseTool):
    """Tool for creating a new task"""

    name: str = "create_task"
    description: str = "Create a new task"
    args_schema: ArgsSchema = CreateTaskInput

    tasks_service: TasksApiService

    def __init__(self, tasks_service: TasksApiService):
        super().__init__(calendar_service=tasks_service)

    def _run(
            self,
            title: str,
            notes: Optional[str] = None,
            due: Optional[str] = None,
            task_list_id: str = "@default",
    ) -> dict:
        """Create a new task"""
        try:
            task = self.tasks_service.create_task(
                title=title,
                notes=notes,
                due=due,
                task_list_id=task_list_id
            )
            return_dict = {
                "status": "success",
                "task_id": task.task_id,
            }
            return return_dict | {
                "title": task.title,
                "due": task.due.strftime("%A, %b %d, %Y"),
                "notes": task.notes,
            }

        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Failed to find event: {str(e)}"
            }


class ListTasksInput(BaseModel):
    """Input schema for listing tasks"""
    tasklist: Optional[str] = Field(default='@default', description="The task list ID to list tasks from, defaults to '@default'")
    max_results: Optional[int] = Field(default=10, description="The maximum number of tasks to return")
    show_completed: Optional[bool] = Field(default=False, description="Whether to include completed tasks")
    due_before: Optional[str] = Field(default=None, description="Return tasks due before this date (YYYY-mm-dd)")
    due_after: Optional[str] = Field(default=None, description="Return tasks due after this date (YYYY-mm-dd)")


class ListTasksTool(BaseTool):
    """Tool for listing tasks"""

    name: str = "list_tasks"
    description: str = "List tasks"
    args_schema: ArgsSchema = ListTasksInput

    tasks_service: TasksApiService

    def __init__(self, tasks_service: TasksApiService):
        super().__init__(tasks_service=tasks_service)

    def _run(
            self,
            tasklist: str = "@default",
            max_results: int = 20,
            show_completed: bool = False,
            due_before: Optional[str] = None,
            due_after: Optional[str] = None,
    ) -> Union[dict, list[dict]]:
        """List tasks"""
        try:
            params = {
                "tasklist": tasklist,
                "max_results": max_results,
                "show_completed": show_completed,
                "due_before": due_before,
                "due_after": due_after,
            }
            builder = query_builder(self.tasks_service, params)
            tasks = builder.execute()
            return [
                {
                    "task_id": task.task_id,
                    "title": task.title,
                    "due": task.due.strftime("%A, %b %d, %Y") if task.due else None,
                    "notes": task.notes,
                    "status": task.status,
                }
                for task in tasks
            ]
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Failed to list tasks: {str(e)}"
            }


class DeleteTaskInput(BaseModel):
    """Input schema for deleting a task"""
    task_id: str = Field(description="The ID of the task to delete")
    tasklist: Optional[str] = Field(default='@default', description="The task list ID the task belongs to, defaults to '@default'")


class DeleteTaskTool(BaseTool):
    """Tool for deleting a task"""

    name: str = "delete_task"
    description: str = "Delete a task"
    args_schema: ArgsSchema = DeleteTaskInput

    tasks_service: TasksApiService

    def __init__(self, tasks_service: TasksApiService):
        super().__init__(tasks_service=tasks_service)

    def _run(self, task_id: str, tasklist: str = "@default") -> dict:
        """Delete a task"""
        try:
            self.tasks_service.delete_task(task=task_id, task_list_id=tasklist)
            return {
                "status": "success",
                "message": f"Task with ID: {task_id} deleted successfully"
            }

        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Failed to delete task: {str(e)}"
            }


class CompleteTaskInput(BaseModel):
    """Input schema for completing a task"""
    task_id: str = Field(description="The ID of the task to complete")
    tasklist: Optional[str] = Field(default='@default', description="The task list ID the task belongs to, defaults to '@default'")


class CompleteTaskTool(BaseTool):
    """Tool for completing a task"""

    name: str = "complete_task"
    description: str = "Mark a task as completed"
    args_schema: ArgsSchema = CompleteTaskInput

    tasks_service: TasksApiService

    def __init__(self, tasks_service: TasksApiService):
        super().__init__(tasks_service=tasks_service)

    def _run(self, task_id: str, tasklist: str = "@default") -> dict:
        """Complete a task"""
        try:
            task = self.tasks_service.mark_completed(task=task_id, task_list_id=tasklist)
            return {
                "status": "success",
                "message": f"Task {task.title} with ID: {task_id} marked as completed"
            }

        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Failed to complete task: {str(e)}"
            }


class ReopenTaskInput(BaseModel):
    """Input schema for reopening a completed task"""
    task_id: str = Field(description="The ID of the task to reopen")
    tasklist: Optional[str] = Field(default='@default', description="The task list ID the task belongs to, defaults to '@default'")


class ReopenTaskTool(BaseTool):
    """Tool for reopening a completed task"""

    name: str = "reopen_task"
    description: str = "Reopen a completed task"
    args_schema: ArgsSchema = ReopenTaskInput

    tasks_service: TasksApiService

    def __init__(self, tasks_service: TasksApiService):
        super().__init__(tasks_service=tasks_service)

    def _run(self, task_id: str, tasklist: str = "@default") -> dict:
        """Reopen a completed task"""
        try:
            task = self.tasks_service.mark_incomplete(task=task_id, task_list_id=tasklist)
            return {
                "status": "success",
                "message": f"Task {task.title} with ID: {task_id} reopened successfully"
            }

        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Failed to reopen task: {str(e)}"
            }


class UpdateTaskInput(BaseModel):
    """Input schema for updating a task"""
    task_id: str = Field(description="The ID of the task to update")
    title: Optional[str] = Field(default=None, description="The new title of the task")
    notes: Optional[str] = Field(default=None, description="The new notes/details of the task")
    due: Optional[str] = Field(default=None, description="The new due date of the task in YYYY-mm-dd format")
    tasklist: Optional[str] = Field(default='@default', description="The task list ID the task belongs to, defaults to '@default'")


class UpdateTaskTool(BaseTool):
    """Tool for updating a task"""

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
            tasklist: str = "@default",
    ) -> dict:
        """Update a task"""
        try:
            task = self.tasks_service.get_task(task_id=task_id)
            if title is not None:
                task.title = title
            if notes is not None:
                task.notes = notes
            if due is not None:
                task.due = datetime.strptime(due, "%Y-%m-%d").date()

            updated_task = self.tasks_service.update_task(task=task, task_list_id=tasklist)
            return {
                "status": "success",
                "task_id": updated_task.task_id,
                "title": updated_task.title,
                "due": updated_task.due.strftime("%A, %b %d, %Y") if updated_task.due else None,
                "notes": updated_task.notes,
            }

        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Failed to update task: {str(e)}"
            }


class CreateTaskListInput(BaseModel):
    """Input schema for creating a new task list"""
    title: str = Field(description="The title of the task list to create")


class CreateTaskListTool(BaseTool):
    """Tool for creating a new task list"""

    name: str = "create_task_list"
    description: str = "Create a new task list"
    args_schema: ArgsSchema = CreateTaskListInput

    tasks_service: TasksApiService

    def __init__(self, tasks_service: TasksApiService):
        super().__init__(tasks_service=tasks_service)

    def _run(self, title: str) -> dict:
        """Create a new task list"""
        try:
            task_list = self.tasks_service.create_task_list(title=title)
            return {
                "status": "success",
                "task_list_id": task_list.task_list_id,
                "title": task_list.title,
                "message": f"Task list created successfully with ID: {task_list.task_list_id} and Title: {task_list.title}"
            }

        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Failed to create task list: {str(e)}"
            }


class ListTaskListsTool(BaseTool):
    """Tool for listing task lists"""

    name: str = "list_task_lists"
    description: str = "List task lists"
    args_schema: ArgsSchema = BaseModel

    tasks_service: TasksApiService

    def __init__(self, tasks_service: TasksApiService):
        super().__init__(tasks_service=tasks_service)

    def _run(self) -> Union[dict, list[dict]]:
        """List task lists"""
        try:
            task_lists = self.tasks_service.list_task_lists()
            return [
                {
                    "task_list_id": task_list.task_list_id,
                    "title": task_list.title,
                    "updated": task_list.updated.strftime("%A, %b %d, %Y") if task_list.updated else None,
                }
                for task_list in task_lists
            ]
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Failed to list task lists: {str(e)}"
            }


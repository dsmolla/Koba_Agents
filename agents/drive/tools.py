from google_client.services.drive.api_service import DriveApiService
from langchain.tools import BaseTool
from typing import Optional, Union

from langchain_core.tools import ArgsSchema
from pydantic import BaseModel, Field
from datetime import datetime


class SearchFilesInput(BaseModel):
    """Input schema for searching files"""
    limit: Optional[int] = Field(default=10, description="Maximum number of files to return")

class SearchFilesTool(BaseTool):
    """Tool for searching files"""

    name: str = "search_files"
    description: str = "Search for files in Google Drive based on multiple criteria"
    args_schema: ArgsSchema = SearchFilesInput

    drive_service: DriveApiService

    def __init__(self, drive_service: DriveApiService):
        super().__init__(drive_service=drive_service)

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


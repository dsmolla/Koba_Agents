import logging
from typing import Annotated

from langchain_core.callbacks import adispatch_custom_event
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import ArgsSchema, InjectedToolArg
from langgraph.types import interrupt
from pydantic import BaseModel, Field

from agents.common.tools import BaseGoogleTool
from core.auth import get_drive_service
from google_client.services.drive.types import DriveFolder

logger = logging.getLogger(__name__)


class MoveFileInput(BaseModel):
    file_ids: list[str] = Field(description="The file_ids or folder_ids to move")
    target_folder_id: str = Field(description="The folder_id of the destination folder")


class MoveFileTool(BaseGoogleTool):
    name: str = "move_file"
    description: str = "Move one or more files or folders to a target folder."
    args_schema: ArgsSchema = MoveFileInput

    def _run(self, file_ids: list[str], target_folder_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, file_ids: list[str], target_folder_id: str) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Moving File...", "icon": "📦"}
        )
        drive = await get_drive_service(config)
        target_folder = await drive.get(target_folder_id)

        if not isinstance(target_folder, DriveFolder):
            return f"Target {target_folder_id} is not a folder"

        results = await drive.batch_move(
            items=file_ids,
            target_folder=target_folder,
            remove_from_current_parents=True
        )
        successes = [r for r in results if not isinstance(r, tuple)]
        errors = [r for r in results if isinstance(r, tuple)]
        msg = f"{len(successes)} item(s) moved to '{target_folder.name}'."
        if errors:
            msg += f" {len(errors)} failed."
        return msg


class RenameFileInput(BaseModel):
    file_id: str = Field(description="The file_id or folder_id to rename")
    new_name: str = Field(description="New name for the file or folder")


class RenameFileTool(BaseGoogleTool):
    name: str = "rename_file"
    description: str = "Rename a file or folder"
    args_schema: ArgsSchema = RenameFileInput

    def _run(self, file_id: str, new_name: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, file_id: str, new_name: str) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Renaming File...", "icon": "✏️"}
        )
        drive = await get_drive_service(config)
        item = await drive.get(file_id)
        updated_item = await drive.rename(item=item, name=new_name)

        return f"Item renamed successfully to '{updated_item.name}'"


class DeleteFileInput(BaseModel):
    file_ids: list[str] = Field(description="The file_ids or folder_ids of the items to delete")


class DeleteFileTool(BaseGoogleTool):
    name: str = "delete_file"
    description: str = "Permanently delete one or more files or folders from Google Drive."
    args_schema: ArgsSchema = DeleteFileInput

    def _run(self, file_ids: list[str], config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, file_ids: list[str]) -> str:
        drive = await get_drive_service(config)

        try:
            items = await drive.batch_get(file_ids)
            data_string = "\n".join([
                f"• {item.name}" if hasattr(item, 'name') else "• Unknown File"
                for i, item in enumerate(items)
            ])
        except Exception:
            data_string = f"{len(file_ids)} file(s) that could not be previewed."

        approval = interrupt({
            "confirmation": f"Are you sure you want to permanently delete these {len(file_ids)} file(s)?",
            "data": data_string
        })

        if not approval or not approval.get("approved"):
            return "File deletion cancelled by user."

        await adispatch_custom_event(
            "tool_status",
            {"text": "Deleting File...", "icon": "🗑️"}
        )
        results = await drive.batch_delete(items=file_ids)
        successes = sum(1 for r in results if r is True)
        errors = sum(1 for r in results if isinstance(r, tuple))
        msg = f"{successes} of {len(file_ids)} item(s) deleted."
        if errors:
            msg += f" {errors} failed."
        return msg
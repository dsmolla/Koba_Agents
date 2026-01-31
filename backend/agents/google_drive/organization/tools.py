import logging
from typing import Annotated

from langchain_core.callbacks import adispatch_custom_event
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import ArgsSchema, InjectedToolArg
from pydantic import BaseModel, Field

from agents.common.tools import BaseGoogleTool
from core.auth import get_drive_service
from google_client.services.drive.types import DriveFolder

logger = logging.getLogger(__name__)


class MoveFileInput(BaseModel):
    file_id: str = Field(description="The file_id or folder_id to move")
    target_folder_id: str = Field(description="The folder_id of the destination folder")


class MoveFileTool(BaseGoogleTool):
    name: str = "move_file"
    description: str = "Move a file or folder to a different folder"
    args_schema: ArgsSchema = MoveFileInput

    def _run(self, file_id: str, target_folder_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, file_id: str, target_folder_id: str) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Moving File...", "icon": "📦"}
        )
        drive = await get_drive_service(config)
        item = await drive.get(file_id)
        target_folder = await drive.get(target_folder_id)

        if not isinstance(target_folder, DriveFolder):
            return f"Target {target_folder_id} is not a folder"

        updated_item = await drive.move(
            item=item,
            target_folder=target_folder,
            remove_from_current_parents=True
        )

        return f"{updated_item.name} moved successfully to folder {target_folder.name}"


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
    file_id: str = Field(description="The file_id or folder_id of the item to delete")


class DeleteFileTool(BaseGoogleTool):
    name: str = "delete_file"
    description: str = "Delete a file or folder from Google Drive permanently"
    args_schema: ArgsSchema = DeleteFileInput

    def _run(self, file_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, file_id: str) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Deleting File...", "icon": "🗑️"}
        )
        drive = await get_drive_service(config)
        item = await drive.get(file_id)
        await drive.delete(item)

        return f"Item deleted successfully. file_id: {file_id}"
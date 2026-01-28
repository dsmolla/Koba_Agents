import logging
from typing import Annotated

from google.auth.exceptions import RefreshError
from google_client.services.drive.types import DriveFolder
from googleapiclient.errors import HttpError
from langchain_core.callbacks import adispatch_custom_event
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import ArgsSchema, InjectedToolArg
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from core.auth import get_drive_service
from core.exceptions import ProviderNotConnectedError

logger = logging.getLogger(__name__)


class MoveFileInput(BaseModel):
    file_id: str = Field(description="The file_id or folder_id to move")
    target_folder_id: str = Field(description="The folder_id of the destination folder")


class MoveFileTool(BaseTool):
    name: str = "move_file"
    description: str = "Move a file or folder to a different folder"
    args_schema: ArgsSchema = MoveFileInput

    def _run(self, file_id: str, target_folder_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(self, file_id: str, target_folder_id: str,
                    config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        try:
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

        except (ProviderNotConnectedError, RefreshError):
            return "I currently don't have access to your drive. Connect Google Drive from the settings page."
        
        except HttpError as e:
            if e.status_code == 403:
                return "I currently don't have access to your drive. Connect Google Drive from the settings page."
            raise e

        except Exception as e:
            logger.error(f"Error in MoveFileTool: {e}", exc_info=True)
            return "Unable to move item due to internal error"


class RenameFileInput(BaseModel):
    file_id: str = Field(description="The file_id or folder_id to rename")
    new_name: str = Field(description="New name for the file or folder")


class RenameFileTool(BaseTool):
    name: str = "rename_file"
    description: str = "Rename a file or folder"
    args_schema: ArgsSchema = RenameFileInput

    def _run(self, file_id: str, new_name: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(self, file_id: str, new_name: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        try:
            await adispatch_custom_event(
                "tool_status",
                {"text": "Renaming File...", "icon": "✏️"}
            )
            drive = await get_drive_service(config)
            item = await drive.get(file_id)
            updated_item = await drive.rename(item=item, name=new_name)

            return f"Item renamed successfully to '{updated_item.name}'"

        except (ProviderNotConnectedError, RefreshError):
            return "I currently don't have access to your drive. Connect Google Drive from the settings page."
        
        except HttpError as e:
            if e.status_code == 403:
                return "I currently don't have access to your drive. Connect Google Drive from the settings page."
            raise e

        except Exception as e:
            logger.error(f"Error in RenameFileTool: {e}", exc_info=True)
            return "Unable to rename item due to internal error"


class DeleteFileInput(BaseModel):
    file_id: str = Field(description="The file_id or folder_id of the item to delete")


class DeleteFileTool(BaseTool):
    name: str = "delete_file"
    description: str = "Delete a file or folder from Google Drive permanently"
    args_schema: ArgsSchema = DeleteFileInput

    def _run(self, file_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(self, file_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        try:
            await adispatch_custom_event(
                "tool_status",
                {"text": "Deleting File...", "icon": "🗑️"}
            )
            drive = await get_drive_service(config)
            item = await drive.get(file_id)
            await drive.delete(item)

            return f"Item deleted successfully. file_id: {file_id}"

        except (ProviderNotConnectedError, RefreshError):
            return "I currently don't have access to your drive. Connect Google Drive from the settings page."
        
        except HttpError as e:
            if e.status_code == 403:
                return "I currently don't have access to your drive. Connect Google Drive from the settings page."
            raise e

        except Exception as e:
            logger.error(f"Error in DeleteFileTool: {e}", exc_info=True)
            return "Unable to delete item due to internal error"

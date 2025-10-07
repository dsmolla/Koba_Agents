from google_client.services.drive.types import DriveFile, DriveFolder, DriveItem
from google_client.services.drive.api_service import DriveApiService
from langchain.tools.base import BaseTool
from langchain_core.tools import ArgsSchema
from pydantic import BaseModel, Field

from shared.exceptions import ToolException
from shared.response import ToolResponse


class MoveFileInput(BaseModel):
    file_id: str = Field(description="The file_id or folder_id to move")
    target_folder_id: str = Field(description="The folder_id of the destination folder")


class MoveFileTool(BaseTool):
    name: str = "move_file"
    description: str = "Move a file or folder to a different folder"
    args_schema: ArgsSchema = MoveFileInput

    drive_service: DriveApiService

    def __init__(self, drive_service: DriveApiService):
        super().__init__(drive_service=drive_service)

    def _run(self, file_id: str, target_folder_id: str) -> ToolResponse:
        try:
            item = self.drive_service.get(file_id)
            target_folder = self.drive_service.get(target_folder_id)

            if not isinstance(target_folder, DriveFolder):
                raise ToolException(
                    tool_name=self.name,
                    message=f"Target {target_folder_id} is not a folder"
                )

            updated_item = self.drive_service.move(
                item=item,
                target_folder=target_folder,
                remove_from_current_parents=True
            )

            return ToolResponse(
                status="success",
                message=f"{updated_item.name} moved successfully to folder {target_folder.name}"
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to move item: {str(e)}"
            )


class RenameFileInput(BaseModel):
    file_id: str = Field(description="The file_id or folder_id to rename")
    new_name: str = Field(description="New name for the file or folder")


class RenameFileTool(BaseTool):
    name: str = "rename_file"
    description: str = "Rename a file or folder"
    args_schema: ArgsSchema = RenameFileInput

    drive_service: DriveApiService

    def __init__(self, drive_service: DriveApiService):
        super().__init__(drive_service=drive_service)

    def _run(self, file_id: str, new_name: str) -> ToolResponse:
        try:
            item = self.drive_service.get(file_id)
            updated_item = self.drive_service.rename(item=item, name=new_name)

            return ToolResponse(
                status="success",
                message=f"Item renamed successfully to '{updated_item.name}'"
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to rename item: {str(e)}"
            )


class DeleteFileInput(BaseModel):
    file_id: str = Field(description="The file_id or folder_id of the item to delete")


class DeleteFileTool(BaseTool):
    name: str = "delete_file"
    description: str = "Delete a file or folder from Google Drive permanently"
    args_schema: ArgsSchema = DeleteFileInput

    drive_service: DriveApiService

    def __init__(self, drive_service: DriveApiService):
        super().__init__(drive_service=drive_service)

    def _run(self, file_id: str) -> ToolResponse:
        try:
            item = self.drive_service.get(file_id)
            self.drive_service.delete(item)

            return ToolResponse(
                status="success",
                message=f"Item deleted successfully. file_id: {file_id}"
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to delete item: {str(e)}"
            )


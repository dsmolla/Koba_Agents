from google_client.services.drive.types import DriveFolder
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import ArgsSchema
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from core.auth import get_drive_service


class MoveFileInput(BaseModel):
    file_id: str = Field(description="The file_id or folder_id to move")
    target_folder_id: str = Field(description="The folder_id of the destination folder")


class MoveFileTool(BaseTool):
    name: str = "move_file"
    description: str = "Move a file or folder to a different folder"
    args_schema: ArgsSchema = MoveFileInput

    def _run(self, file_id: str, target_folder_id: str, config: RunnableConfig) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(self, file_id: str, target_folder_id: str, config: RunnableConfig) -> str:
        try:
            service = get_drive_service(config)
            item = await service.get(file_id)
            target_folder = await service.get(target_folder_id)

            if not isinstance(target_folder, DriveFolder):
                return f"Target {target_folder_id} is not a folder"

            updated_item = await service.move(
                item=item,
                target_folder=target_folder,
                remove_from_current_parents=True
            )

            return f"{updated_item.name} moved successfully to folder {target_folder.name}"

        except Exception as e:
            return "Unable to move item due to internal error"


class RenameFileInput(BaseModel):
    file_id: str = Field(description="The file_id or folder_id to rename")
    new_name: str = Field(description="New name for the file or folder")


class RenameFileTool(BaseTool):
    name: str = "rename_file"
    description: str = "Rename a file or folder"
    args_schema: ArgsSchema = RenameFileInput

    def _run(self, file_id: str, new_name: str, config: RunnableConfig) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(self, file_id: str, new_name: str, config: RunnableConfig) -> str:
        try:
            service = get_drive_service(config)
            item = await service.get(file_id)
            updated_item = await service.rename(item=item, name=new_name)

            return f"Item renamed successfully to '{updated_item.name}'"

        except Exception as e:
            return "Unable to rename item due to internal error"


class DeleteFileInput(BaseModel):
    file_id: str = Field(description="The file_id or folder_id of the item to delete")


class DeleteFileTool(BaseTool):
    name: str = "delete_file"
    description: str = "Delete a file or folder from Google Drive permanently"
    args_schema: ArgsSchema = DeleteFileInput

    def _run(self, file_id: str, config: RunnableConfig) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(self, file_id: str, config: RunnableConfig) -> str:
        try:
            service = get_drive_service(config)
            item = await service.get(file_id)
            await service.delete(item)

            return f"Item deleted successfully. file_id: {file_id}"

        except Exception as e:
            return "Unable to delete item due to internal error"

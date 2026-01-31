import logging
import shutil
from typing import Optional, Literal, Annotated

from google.auth.exceptions import RefreshError
from google_client.services.drive.types import DriveFolder
from googleapiclient.errors import HttpError
from langchain_core.callbacks import adispatch_custom_event
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import ArgsSchema, InjectedToolArg
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from agents.common.download_supabase_to_disk import download_to_disk
from core.auth import get_drive_service
from core.exceptions import ProviderNotConnectedError

logger = logging.getLogger(__name__)


class UploadFileInput(BaseModel):
    file_path: str = Field(description="Local path to the file to upload")
    name: Optional[str] = Field(default=None, description="Name for the file in Drive (defaults to filename)")
    parent_folder_id: Optional[str] = Field(default=None, description="ID of parent folder to upload to")
    description: Optional[str] = Field(default=None, description="File description")


class UploadFileTool(BaseTool):
    name: str = "upload_file"
    description: str = "Upload a file to Google Drive"
    args_schema: ArgsSchema = UploadFileInput

    def _run(
            self,
            file_path: str,
            config: Annotated[RunnableConfig, InjectedToolArg],
            name: Optional[str] = None,
            parent_folder_id: Optional[str] = None,
            description: Optional[str] = None
    ) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(
            self,
            file_path: str,
            config: Annotated[RunnableConfig, InjectedToolArg],
            name: Optional[str] = None,
            parent_folder_id: Optional[str] = None,
            description: Optional[str] = None
    ) -> str:
        folder = None
        try:
            await adispatch_custom_event(
                "tool_status",
                {"text": "Uploading File...", "icon": "⬆️"}
            )
            drive = await get_drive_service(config)
            folder, downloaded_file = await download_to_disk([file_path])
            if not downloaded_file:
                return "Failed to download file from storage."
                
            file = await drive.upload_file(
                file_path=downloaded_file[0],
                name=name,
                parent_folder_id=parent_folder_id,
                description=description
            )

            return f"File uploaded successfully. file_id: {file.file_id}, name: {file.name}"

        except (ProviderNotConnectedError, RefreshError):
            return "I currently don't have access to your drive. Connect Google Drive from the settings page."
        
        except HttpError as e:
            if e.status_code == 403:
                return "I currently don't have access to your drive. Connect Google Drive from the settings page."
            raise e

        except Exception as e:
            logger.error(f"Error in UploadFileTool: {e}", exc_info=True)
            return "Unable to upload file due to internal error"
        finally:
            if folder and folder.exists():
                shutil.rmtree(folder)


class CreateFolderInput(BaseModel):
    name: str = Field(description="Name of the folder to create")
    parent_folder_id: Optional[str] = Field(default=None, description="ID of parent folder")
    description: Optional[str] = Field(default=None, description="Folder description")


class CreateFolderTool(BaseTool):
    name: str = "create_folder"
    description: str = "Create a new folder in Google Drive"
    args_schema: ArgsSchema = CreateFolderInput

    def _run(
            self,
            name: str,
            config: Annotated[RunnableConfig, InjectedToolArg],
            parent_folder_id: Optional[str] = None,
            description: Optional[str] = None
    ) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(
            self,
            name: str,
            config: Annotated[RunnableConfig, InjectedToolArg],
            parent_folder_id: Optional[str] = None,
            description: Optional[str] = None
    ) -> str:
        try:
            await adispatch_custom_event(
                "tool_status",
                {"text": "Creating Folder...", "icon": "📁"}
            )
            drive = await get_drive_service(config)
            parent_folder = None
            if parent_folder_id:
                parent_folder = await drive.get(parent_folder_id)
                if not isinstance(parent_folder, DriveFolder):
                    return f"Parent ID {parent_folder_id} is not a folder"

            folder = await drive.create_folder(
                name=name,
                parent_folder=parent_folder,
                description=description
            )

            return f"Folder created successfully. folder_id: {folder.folder_id}, name: {folder.name}"

        except (ProviderNotConnectedError, RefreshError):
            return "I currently don't have access to your drive. Connect Google Drive from the settings page."
        
        except HttpError as e:
            if e.status_code == 403:
                return "I currently don't have access to your drive. Connect Google Drive from the settings page."
            raise e

        except Exception as e:
            logger.error(f"Error in CreateFolderTool: {e}", exc_info=True)
            return "Unable to create folder due to internal error"


class ShareFileInput(BaseModel):
    file_id: str = Field(description="The file_id or folder_id to share")
    email: str = Field(description="Email address of the user to share with")
    role: Literal["reader", "writer", "commenter"] = Field(
        default="reader",
        description="Permission role: 'reader' (view only), 'writer' (can edit), 'commenter' (can comment)"
    )
    notify: bool = Field(default=True, description="Whether to send notification email")
    message: Optional[str] = Field(default=None, description="Custom message in notification email")


class ShareFileTool(BaseTool):
    name: str = "share_file"
    description: str = "Share a file or folder with a user by email"
    args_schema: ArgsSchema = ShareFileInput

    def _run(
            self,
            file_id: str,
            email: str,
            config: Annotated[RunnableConfig, InjectedToolArg],
            role: str = "reader",
            notify: bool = True,
            message: Optional[str] = None
    ) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(
            self,
            file_id: str,
            email: str,
            config: Annotated[RunnableConfig, InjectedToolArg],
            role: str = "reader",
            notify: bool = True,
            message: Optional[str] = None
    ) -> str:
        try:
            await adispatch_custom_event(
                "tool_status",
                {"text": "Sharing File...", "icon": "🤝"}
            )
            drive = await get_drive_service(config)
            item = await drive.get(file_id)
            permission = await drive.share(
                item=item,
                email=email,
                role=role,
                notify=notify,
                message=message
            )

            return f"File shared successfully with {email} as {role}. permission_id: {permission.permission_id}"

        except (ProviderNotConnectedError, RefreshError):
            return "I currently don't have access to your drive. Connect Google Drive from the settings page."
        
        except HttpError as e:
            if e.status_code == 403:
                return "I currently don't have access to your drive. Connect Google Drive from the settings page."
            raise e

        except Exception as e:
            logger.error(f"Error in ShareFileTool: {e}", exc_info=True)
            return "Unable to share file due to internal error"

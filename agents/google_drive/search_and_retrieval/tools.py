import json
import os
from datetime import datetime
from typing import Optional, Annotated

from google_client.services.drive.types import DriveFile, DriveFolder, DriveItem
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import ArgsSchema, InjectedToolArg
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from langchain_core.callbacks import adispatch_custom_event

from core.auth import get_drive_service


class SearchFilesInput(BaseModel):
    query: Optional[str] = Field(default=None, description="Search query to find files by name or content")
    max_results: Optional[int] = Field(default=10, description="Maximum number of files to return")
    extension: Optional[str] = Field(default=None,
                                     description="Filter by extension type (e.g., 'pdf', 'docx', 'xlsx', 'jpg', 'mp4')")
    folder_id: Optional[str] = Field(default=None, description="Search within a specific folder by folder_id")
    include_trashed: Optional[bool] = Field(default=False, description="Include trashed files or not")
    owned_by_me: Optional[bool] = Field(default=None, description="Filter files owned by me/user")
    shared_with_me: Optional[bool] = Field(default=None, description="Filter for files shared with the user")
    modified_after: Optional[str] = Field(default=None,
                                          description="ISO format date string to filter files modified after this date")
    modified_before: Optional[str] = Field(default=None,
                                           description="ISO format date string to filter files modified before this date")
    created_after: Optional[str] = Field(default=None,
                                         description="ISO format date string to filter files created after this date")
    created_before: Optional[str] = Field(default=None,
                                          description="ISO format date string to filter files created before this date")
    starred: Optional[bool] = Field(default=None, description="Filter for starred/unstarred items")
    include_folders: Optional[bool] = Field(default=True, description="Whether to include folders in results")
    include_files: Optional[bool] = Field(default=True, description="Whether to include files in results")
    order_by: Optional[str] = Field(default=None,
                                    description="Order results by field (e.g., 'modifiedTime desc', 'name', 'createdTime')")


class SearchFilesTool(BaseTool):
    name: str = "search_files"
    description: str = (
        "Search for files and folders in Google Drive with extensive filtering options. "
        "Can filter by name, content, file type, folder location, owner, sharing status, "
        "modification/creation dates, starred status, and more."
    )
    args_schema: ArgsSchema = SearchFilesInput

    def _run(
            self,
            config: Annotated[RunnableConfig, InjectedToolArg],
            query: Optional[str] = None,
            max_results: Optional[int] = 10,
            extension: Optional[str] = None,
            folder_id: Optional[str] = None,
            include_trashed: Optional[bool] = False,
            owned_by_me: Optional[bool] = None,
            shared_with_me: Optional[bool] = None,
            is_shared: Optional[bool] = None,
            modified_after: Optional[str] = None,
            modified_before: Optional[str] = None,
            created_after: Optional[str] = None,
            created_before: Optional[str] = None,
            starred: Optional[bool] = None,
            include_folders: Optional[bool] = True,
            include_files: Optional[bool] = True,
            order_by: Optional[str] = None
    ) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(
            self,
            config: Annotated[RunnableConfig, InjectedToolArg],
            query: Optional[str] = None,
            max_results: Optional[int] = 10,
            extension: Optional[str] = None,
            folder_id: Optional[str] = None,
            include_trashed: Optional[bool] = False,
            owned_by_me: Optional[bool] = None,
            shared_with_me: Optional[bool] = None,
            is_shared: Optional[bool] = None,
            modified_after: Optional[str] = None,
            modified_before: Optional[str] = None,
            created_after: Optional[str] = None,
            created_before: Optional[str] = None,
            starred: Optional[bool] = None,
            include_folders: Optional[bool] = True,
            include_files: Optional[bool] = True,
            order_by: Optional[str] = None
    ) -> str:
        try:
            await adispatch_custom_event(
                "tool_status",
                {"text": "Searching Files...", "icon": "🔍"}
            )
            drive = await get_drive_service(config)
            builder = drive.query()

            if max_results:
                builder = builder.limit(max_results)
            if query:
                builder = builder.search(query)
            if extension:
                builder = builder.with_extension(extension)
            if folder_id:
                builder = builder.in_folder(folder_id)
            builder = builder.trashed(include_trashed)
            if owned_by_me:
                builder = builder.owned_by_me()
            if shared_with_me:
                builder = builder.shared_with_me()
            if modified_after:
                builder = builder.modified_after(datetime.fromisoformat(modified_after))
            if modified_before:
                builder = builder.modified_before(datetime.fromisoformat(modified_before))
            if created_after:
                builder = builder.created_after(datetime.fromisoformat(created_after))
            if created_before:
                builder = builder.created_before(datetime.fromisoformat(created_before))
            if starred:
                builder = builder.starred()
            if not include_folders and include_files:
                builder = builder.files_only()
            elif include_folders and not include_files:
                builder = builder.folders_only()
            elif not include_folders and not include_files:
                return "Cannot exclude both files and folders"

            items = await builder.execute()
            items_data = [self._item_to_dict(item) for item in items]

            return json.dumps(items_data)

        except Exception as e:
            return "Unable to search files due to internal error"

    def _item_to_dict(self, item: DriveItem) -> dict:
        """Convert DriveItem to dict representation"""
        base_dict = {
            "id": item.item_id,
            "name": item.name,
            "type": "folder" if isinstance(item, DriveFolder) else "file",
            "created_time": item.created_time.isoformat() if item.created_time else None,
            "modified_time": item.modified_time.isoformat() if item.modified_time else None,
            "web_view_link": item.web_view_link,
            "starred": item.starred,
            "trashed": item.trashed,
            "shared": item.shared,
            "owners": item.owners,
        }

        if isinstance(item, DriveFile):
            base_dict.update({
                "mime_type": item.mime_type,
                "size": item.size,
                "size_readable": item.human_readable_size() if item.size else None,
                "file_extension": item.file_extension,
            })

        return base_dict


class GetFileInput(BaseModel):
    file_id: str = Field(description="The file_id or folder_id of the item to retrieve")


class GetFileTool(BaseTool):
    name: str = "get_file"
    description: str = "Get detailed information about a specific file or folder by its ID"
    args_schema: ArgsSchema = GetFileInput

    def _run(self, file_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(self, file_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        try:
            await adispatch_custom_event(
                "tool_status",
                {"text": "Retrieving File Metadata...", "icon": "📄"}
            )
            drive = await get_drive_service(config)
            item = await drive.get(file_id)

            item_dict = {
                "id": item.item_id,
                "name": item.name,
                "type": "folder" if isinstance(item, DriveFolder) else "file",
                "created_time": item.created_time.isoformat() if item.created_time else None,
                "modified_time": item.modified_time.isoformat() if item.modified_time else None,
                "web_view_link": item.web_view_link,
                "parent_ids": item.parent_ids,
                "owners": item.owners,
                "starred": item.starred,
                "trashed": item.trashed,
                "shared": item.shared,
                "description": item.description,
            }

            if isinstance(item, DriveFile):
                item_dict.update({
                    "mime_type": item.mime_type,
                    "size": item.size,
                    "size_readable": item.human_readable_size() if item.size else None,
                    "file_extension": item.file_extension,
                })

            return json.dumps(item_dict)

        except Exception as e:
            return "Unable to get file due to internal error"


class DownloadFileInput(BaseModel):
    file_id: str = Field(description="The file_id of the file to download")


class DownloadFileTool(BaseTool):
    name: str = "download_file"
    description: str = "Download file content from Google Drive as bytes"
    args_schema: ArgsSchema = DownloadFileInput

    def _run(self, file_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(self, file_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        try:
            await adispatch_custom_event(
                "tool_status",
                {"text": "Downloading File...", "icon": "⬇️"}
            )
            drive = await get_drive_service(config)
            download_folder = config['configurable'].get('download_folder')
            file = await drive.get(file_id)
            if not isinstance(file, DriveFile):
                return f"Item {file_id} is a folder, not a file"

            downloaded_path = await drive.download_file(file, download_folder)
            return f"File downloaded successfully. File Path: {downloaded_path}"
        except Exception as e:
            return "Unable to download file due to internal error"


class ListFolderContentsInput(BaseModel):
    folder_id: str = Field(description="The folder_id to list contents of")
    max_results: Optional[int] = Field(default=100, description="Maximum number of items to return")
    include_files: bool = Field(default=True, description="Whether to include files")
    include_folders: bool = Field(default=True, description="Whether to include subfolders")


class ListFolderContentsTool(BaseTool):
    name: str = "list_folder_contents"
    description: str = "List all files and folders within a specific folder"
    args_schema: ArgsSchema = ListFolderContentsInput

    def _run(
            self,
            folder_id: str,
            config: Annotated[RunnableConfig, InjectedToolArg],
            max_results: Optional[int] = 100,
            include_files: bool = True,
            include_folders: bool = True
    ) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(
            self,
            folder_id: str,
            config: Annotated[RunnableConfig, InjectedToolArg],
            max_results: Optional[int] = 100,
            include_files: bool = True,
            include_folders: bool = True
    ) -> str:
        try:
            await adispatch_custom_event(
                "tool_status",
                {"text": "Listing Folder Contents...", "icon": "📂"}
            )
            drive = await get_drive_service(config)
            folder = await drive.get(folder_id)
            if not isinstance(folder, DriveFolder):
                return f"Item {folder_id} is not a folder"

            contents = await drive.list_folder_contents(
                folder=folder,
                include_files=include_files,
                include_folders=include_folders,
                max_results=max_results
            )

            items_data = [self._item_to_dict(item) for item in contents]

            return json.dumps(items_data)

        except Exception as e:
            return "Unable to list folder contents due to internal error"

    def _item_to_dict(self, item: DriveItem) -> dict:
        base_dict = {
            "id": item.item_id,
            "name": item.name,
            "type": "folder" if isinstance(item, DriveFolder) else "file",
        }

        if isinstance(item, DriveFile):
            base_dict.update({
                "mime_type": item.mime_type,
                "size": item.size,
                "size_readable": item.human_readable_size() if item.size else None,
            })

        return base_dict


class GetPermissionsInput(BaseModel):
    file_id: str = Field(description="The file_id or folder_id to get permissions for")


class GetPermissionsTool(BaseTool):
    name: str = "get_permissions"
    description: str = "Get all sharing permissions for a file or folder"
    args_schema: ArgsSchema = GetPermissionsInput

    def _run(self, file_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(self, file_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        try:
            await adispatch_custom_event(
                "tool_status",
                {"text": "Retrieving Permissions...", "icon": "🔒"}
            )
            drive = await get_drive_service(config)
            item = await drive.get(file_id)
            permissions = await drive.get_permissions(item)

            permissions_data = [
                {
                    "id": perm.permission_id,
                    "type": perm.type,
                    "role": perm.role,
                    "email": perm.email_address,
                    "display_name": perm.display_name,
                    "domain": perm.domain,
                }
                for perm in permissions
            ]

            return json.dumps(permissions_data)

        except Exception as e:
            return "Unable to get permissions due to internal error"

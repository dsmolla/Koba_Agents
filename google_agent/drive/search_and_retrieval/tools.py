import json
import os
from datetime import datetime
from typing import Optional

from google_client.api_service import APIServiceLayer
from google_client.services.drive.types import DriveFile, DriveFolder, DriveItem
from langchain.tools.base import BaseTool
from langchain_core.tools import ArgsSchema
from pydantic import BaseModel, Field

from google_agent.shared.exceptions import ToolException
from google_agent.shared.response import ToolResponse


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

    google_service: APIServiceLayer

    def __init__(self, google_service: APIServiceLayer):
        super().__init__(google_service=google_service)

    def _run(
            self,
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
    ) -> ToolResponse:
        try:
            builder = self.google_service.drive.query()

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
                raise ToolException(
                    tool_name=self.name,
                    message="Cannot exclude both files and folders"
                )

            items = builder.execute()
            items_data = [self._item_to_dict(item) for item in items]

            return ToolResponse(
                status="success",
                message=json.dumps(items_data)
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to search files: {str(e)}"
            )

    async def _arun(
            self,
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
    ) -> ToolResponse:
        try:
            service = self.google_service.async_drive
            builder = service.query()

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
                raise ToolException(
                    tool_name=self.name,
                    message="Cannot exclude both files and folders"
                )

            items = await builder.execute()
            items_data = [self._item_to_dict(item) for item in items]

            return ToolResponse(
                status="success",
                message=json.dumps(items_data)
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to search files: {str(e)}"
            )

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

    google_service: APIServiceLayer

    def __init__(self, google_service: APIServiceLayer):
        super().__init__(google_service=google_service)

    def _run(self, file_id: str) -> ToolResponse:
        try:
            item = self.google_service.drive.get(file_id)

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

            return ToolResponse(
                status="success",
                message=json.dumps(item_dict)
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to get file: {str(e)}"
            )

    async def _arun(self, file_id: str) -> ToolResponse:
        try:
            service = self.google_service.async_drive
            item = await service.get(file_id)

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

            return ToolResponse(
                status="success",
                message=json.dumps(item_dict)
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to get file: {str(e)}"
            )


class DownloadFileInput(BaseModel):
    file_id: str = Field(description="The file_id of the file to download")


class DownloadFileTool(BaseTool):
    name: str = "download_file"
    description: str = "Download file content from Google Drive as bytes"
    args_schema: ArgsSchema = DownloadFileInput

    google_service: APIServiceLayer

    def __init__(self, google_service: APIServiceLayer):
        super().__init__(google_service=google_service)

    def _run(self, file_id: str) -> ToolResponse:
        try:
            file = self.google_service.drive.get(file_id)
            if not isinstance(file, DriveFile):
                raise ToolException(
                    tool_name=self.name,
                    message=f"Item {file_id} is a folder, not a file"
                )

            download_folder = os.path.join(os.path.expanduser("~"), "Downloads", "GoogleDriveFiles")
            downloaded_path = self.google_service.drive.download_file(file, download_folder)

            return ToolResponse(
                status="success",
                message=f"File downloaded successfully. File Path: {downloaded_path}",
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to download file: {str(e)}"
            )

    async def _arun(self, file_id: str) -> ToolResponse:
        try:
            service = self.google_service.async_drive
            file = await service.get(file_id)
            if not isinstance(file, DriveFile):
                raise ToolException(
                    tool_name=self.name,
                    message=f"Item {file_id} is a folder, not a file"
                )

            download_folder = os.path.join(os.path.expanduser("~"), "Downloads", "GoogleDriveFiles")
            downloaded_path = await service.download_file(file, download_folder)

            return ToolResponse(
                status="success",
                message=f"File downloaded successfully. File Path: {downloaded_path}",
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to download file: {str(e)}"
            )


class ListFolderContentsInput(BaseModel):
    folder_id: str = Field(description="The folder_id to list contents of")
    max_results: Optional[int] = Field(default=100, description="Maximum number of items to return")
    include_files: bool = Field(default=True, description="Whether to include files")
    include_folders: bool = Field(default=True, description="Whether to include subfolders")


class ListFolderContentsTool(BaseTool):
    name: str = "list_folder_contents"
    description: str = "List all files and folders within a specific folder"
    args_schema: ArgsSchema = ListFolderContentsInput

    google_service: APIServiceLayer

    def __init__(self, google_service: APIServiceLayer):
        super().__init__(google_service=google_service)

    def _run(
            self,
            folder_id: str,
            max_results: Optional[int] = 100,
            include_files: bool = True,
            include_folders: bool = True
    ) -> ToolResponse:
        try:
            folder = self.google_service.drive.get(folder_id)
            if not isinstance(folder, DriveFolder):
                raise ToolException(
                    tool_name=self.name,
                    message=f"Item {folder_id} is not a folder"
                )

            contents = self.google_service.drive.list_folder_contents(
                folder=folder,
                include_files=include_files,
                include_folders=include_folders,
                max_results=max_results
            )

            items_data = [self._item_to_dict(item) for item in contents]

            return ToolResponse(
                status="success",
                message=json.dumps(items_data)
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to list folder contents: {str(e)}"
            )

    async def _arun(
            self,
            folder_id: str,
            max_results: Optional[int] = 100,
            include_files: bool = True,
            include_folders: bool = True
    ) -> ToolResponse:
        try:
            service = self.google_service.async_drive
            folder = await service.get(folder_id)
            if not isinstance(folder, DriveFolder):
                raise ToolException(
                    tool_name=self.name,
                    message=f"Item {folder_id} is not a folder"
                )

            contents = await service.list_folder_contents(
                folder=folder,
                include_files=include_files,
                include_folders=include_folders,
                max_results=max_results
            )

            items_data = [self._item_to_dict(item) for item in contents]

            return ToolResponse(
                status="success",
                message=json.dumps(items_data)
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to list folder contents: {str(e)}"
            )

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

    google_service: APIServiceLayer

    def __init__(self, google_service: APIServiceLayer):
        super().__init__(google_service=google_service)

    def _run(self, file_id: str) -> ToolResponse:
        try:
            item = self.google_service.drive.get(file_id)
            permissions = self.google_service.drive.get_permissions(item)

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

            return ToolResponse(
                status="success",
                message=json.dumps(permissions_data)
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to get permissions: {str(e)}"
            )

    async def _arun(self, file_id: str) -> ToolResponse:
        try:
            service = self.google_service.async_drive
            item = await service.get(file_id)
            permissions = await service.get_permissions(item)

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

            return ToolResponse(
                status="success",
                message=json.dumps(permissions_data)
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to get permissions: {str(e)}"
            )

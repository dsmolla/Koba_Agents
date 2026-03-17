import asyncio
import json
import logging
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Annotated

import filetype
from google_client.services.drive.types import DriveFile, DriveFolder, DriveItem
from langchain_core.callbacks import adispatch_custom_event
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import ArgsSchema, InjectedToolArg
from pydantic import BaseModel, Field

from agents.common.tools import BaseGoogleTool
from core.auth import get_drive_service, get_gmail_service
from core.cache import get_email_cache
from core.supabase_client import upload_to_supabase

logger = logging.getLogger(__name__)


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


class SearchFilesTool(BaseGoogleTool):
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

    async def _run_google_task(
            self,
            config: RunnableConfig,
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


class GetFileTool(BaseGoogleTool):
    name: str = "get_file"
    description: str = "Get detailed information about a specific file or folder by its ID"
    args_schema: ArgsSchema = GetFileInput

    def _run(self, file_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, file_id: str) -> str:
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


class DownloadFileInput(BaseModel):
    file_id: str = Field(description="The file_id of the file to download")


class DownloadFileTool(BaseGoogleTool):
    name: str = "download_file"
    description: str = "Download file content from Google Drive as bytes"
    args_schema: ArgsSchema = DownloadFileInput

    def _run(self, file_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, file_id: str) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Downloading File...", "icon": "⬇️"}
        )
        drive = await get_drive_service(config)
        user_id = config['configurable'].get('thread_id')
        file = await drive.get(file_id)
        if not isinstance(file, DriveFile):
            return f"Item {file_id} is a folder, not a file"

        file_uuid = uuid.uuid4().hex[:4]
        file_path = Path(file.name)
        filename = f"{file_path.stem}_{file_uuid}{file_path.suffix}"
        upload_path = f"{user_id}/{filename}"
        file_bytes = await drive.get_file_payload(file)
        mime_type = filetype.guess_mime(file_bytes)
        size = len(file_bytes)

        storage_path = await upload_to_supabase(
            path=upload_path,
            file_bytes=file_bytes,
        )
        file_dict = {
            "filename": filename,
            "path": storage_path,
            "mime_type": mime_type,
            "size": size,
        }

        return json.dumps(file_dict)


class ListFolderContentsInput(BaseModel):
    folder_id: str = Field(description="The folder_id to list contents of")
    max_results: Optional[int] = Field(default=100, description="Maximum number of items to return")
    include_files: bool = Field(default=True, description="Whether to include files")
    include_folders: bool = Field(default=True, description="Whether to include subfolders")


class ListFolderContentsTool(BaseGoogleTool):
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

    async def _run_google_task(
            self,
            config: RunnableConfig,
            folder_id: str,
            max_results: Optional[int] = 100,
            include_files: bool = True,
            include_folders: bool = True
    ) -> str:
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


class GetPermissionsTool(BaseGoogleTool):
    name: str = "get_permissions"
    description: str = "Get all sharing permissions for a file or folder"
    args_schema: ArgsSchema = GetPermissionsInput

    def _run(self, file_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, file_id: str) -> str:
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


class SaveAttachmentToDriveInput(BaseModel):
    message_id: str = Field(description="Message ID of the email containing the attachment")
    attachment_id: Optional[str] = Field(default=None,
                                         description="ID of the attachment to save. Leave empty to save all attachments in the email")
    folder_id: Optional[str] = Field(default=None,
                                     description="Drive folder_id to save the attachment into. Saves to root if not specified")


class SaveAttachmentToDriveTool(BaseGoogleTool):
    name: str = "save_attachment_to_drive"
    description: str = "Save one or all email attachments directly to Google Drive, bypassing intermediate storage"
    args_schema: ArgsSchema = SaveAttachmentToDriveInput

    def _run(self, message_id: str, attachment_id: Optional[str] = None,
             folder_id: Optional[str] = None,
             config: Annotated[RunnableConfig, InjectedToolArg] = None) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, message_id: str,
                               attachment_id: Optional[str] = None,
                               folder_id: Optional[str] = None) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Saving Attachment to Drive...", "icon": "📎"}
        )
        gmail = await get_gmail_service(config)
        drive = await get_drive_service(config)
        email_cache = get_email_cache(config)

        email = email_cache.get(message_id)
        if email is None:
            email = email_cache.save(await gmail.get_email(message_id))

        if attachment_id is None:
            target_attachments = email["attachments"]
        else:
            target_attachments = [a for a in email["attachments"] if a["attachment_id"] == attachment_id]

        if not target_attachments:
            return "No matching attachments found."

        async def upload_one(attachment):
            attachment_data = {
                "message_id": message_id,
                "attachment_id": attachment["attachment_id"],
            }
            attachment_bytes = await gmail.get_attachment_payload(attachment_data)
            suffix = Path(attachment["filename"]).suffix
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(attachment_bytes)
                tmp_path = Path(tmp.name)
            try:
                file = await drive.upload_file(
                    file_path=tmp_path,
                    name=attachment["filename"],
                    parent_folder_id=folder_id,
                )
                return {"filename": attachment["filename"], "file_id": file.file_id, "name": file.name}
            finally:
                tmp_path.unlink(missing_ok=True)

        results = await asyncio.gather(*[upload_one(a) for a in target_attachments], return_exceptions=True)

        successes = [r for r in results if not isinstance(r, Exception)]
        for err in results:
            if isinstance(err, Exception):
                logger.error(f"Failed to save attachment to Drive: {err}")

        return json.dumps(successes)

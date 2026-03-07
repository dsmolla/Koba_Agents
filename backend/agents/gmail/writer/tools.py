import logging
import shutil
import tempfile
from pathlib import Path
from typing import Optional, List, Annotated

from langchain_core.callbacks import adispatch_custom_event
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import ArgsSchema, InjectedToolArg
from pydantic import BaseModel, Field

from agents.common.download_supabase_to_disk import download_to_disk
from agents.common.tools import BaseGoogleTool
from core.auth import get_gmail_service, get_drive_service

logger = logging.getLogger(__name__)


async def _download_drive_files(config: RunnableConfig, drive_file_ids: List[str]) -> tuple[Path, List[Path]]:
    """Download Drive files to a temp directory. Returns (temp_dir, list of file paths)."""
    drive = await get_drive_service(config)
    tmp_dir = Path(tempfile.mkdtemp())
    paths = []
    for file_id in drive_file_ids:
        item = await drive.get(file_id)
        file_bytes = await drive.get_file_payload(item)
        dest = tmp_dir / item.name
        dest.write_bytes(file_bytes)
        paths.append(dest)
    return tmp_dir, paths


class WriteEmailInput(BaseModel):
    to: List[str] = Field(description="List of recipient email addresses")
    subject: Optional[str] = Field(default=None, description="Subject line of the email")
    body_text: Optional[str] = Field(default=None, description="Plain text body of the email")
    cc: Optional[List[str]] = Field(default=None, description="List of CC recipient email addresses")
    bcc: Optional[List[str]] = Field(default=None, description="List of BCC recipient email addresses")
    attachment_paths: Optional[List[str]] = Field(default=None, description="List of Supabase file paths to attach")
    drive_file_ids: Optional[List[str]] = Field(default=None, description="List of Google Drive file IDs to attach")


class SendEmailTool(BaseGoogleTool):
    name: str = "send_email"
    description: str = "Send an email through Gmail to one or more recipients"
    args_schema: ArgsSchema = WriteEmailInput

    def _run(
            self,
            to: List[str],
            config: Annotated[RunnableConfig, InjectedToolArg],
            subject: Optional[str] = None,
            body_text: Optional[str] = None,
            cc: Optional[List[str]] = None,
            bcc: Optional[List[str]] = None,
            attachment_paths: Optional[List[str]] = None,
            drive_file_ids: Optional[List[str]] = None
    ) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(
            self,
            config: RunnableConfig,
            to: List[str],
            subject: Optional[str] = None,
            body_text: Optional[str] = None,
            cc: Optional[List[str]] = None,
            bcc: Optional[List[str]] = None,
            attachment_paths: Optional[List[str]] = None,
            drive_file_ids: Optional[List[str]] = None
    ) -> str:
        supabase_folder = None
        drive_folder = None
        try:
            await adispatch_custom_event(
                "tool_status",
                {"text": "Sending Email...", "icon": "📤"}
            )
            gmail = await get_gmail_service(config)
            all_attachments = []
            if attachment_paths:
                supabase_folder, supabase_files = await download_to_disk(attachment_paths)
                all_attachments.extend(supabase_files)
            if drive_file_ids:
                drive_folder, drive_files = await _download_drive_files(config, drive_file_ids)
                all_attachments.extend(drive_files)

            email = await gmail.send_email(
                to=to,
                subject=subject,
                body_text=body_text,
                cc=cc,
                bcc=bcc,
                attachment_paths=all_attachments or None,
            )

            return f"Email sent successfully. message_id: {email.message_id}, thread_id: {email.thread_id}"
        finally:
            if supabase_folder and supabase_folder.exists():
                shutil.rmtree(supabase_folder)
            if drive_folder and drive_folder.exists():
                shutil.rmtree(drive_folder)


class DraftEmailTool(BaseGoogleTool):
    name: str = "draft_email"
    description: str = "Create an email draft in Gmail"
    args_schema: ArgsSchema = WriteEmailInput

    def _run(
            self,
            to: List[str],
            config: Annotated[RunnableConfig, InjectedToolArg],
            subject: Optional[str] = None,
            body_text: Optional[str] = None,
            body_html: Optional[str] = None,
            cc: Optional[List[str]] = None,
            bcc: Optional[List[str]] = None,
            attachment_paths: Optional[List[str]] = None,
            drive_file_ids: Optional[List[str]] = None
    ) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(
            self,
            config: RunnableConfig,
            to: List[str],
            subject: Optional[str] = None,
            body_text: Optional[str] = None,
            body_html: Optional[str] = None,
            cc: Optional[List[str]] = None,
            bcc: Optional[List[str]] = None,
            attachment_paths: Optional[List[str]] = None,
            drive_file_ids: Optional[List[str]] = None
    ) -> str:
        supabase_folder = None
        drive_folder = None
        try:
            await adispatch_custom_event(
                "tool_status",
                {"text": "Creating Draft...", "icon": "📝"}
            )
            gmail = await get_gmail_service(config)
            all_attachments = []
            if attachment_paths:
                supabase_folder, supabase_files = await download_to_disk(attachment_paths)
                all_attachments.extend(supabase_files)
            if drive_file_ids:
                drive_folder, drive_files = await _download_drive_files(config, drive_file_ids)
                all_attachments.extend(drive_files)

            draft = await gmail.create_draft(
                to=to,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                cc=cc,
                bcc=bcc,
                attachment_paths=all_attachments or None,
            )

            return f"Draft created successfully. message_id: {draft.message_id}, thread_id: {draft.thread_id}"
        finally:
            if supabase_folder and supabase_folder.exists():
                shutil.rmtree(supabase_folder)
            if drive_folder and drive_folder.exists():
                shutil.rmtree(drive_folder)


class ReplyEmailInput(BaseModel):
    message_id: str = Field(description="message_id of the email to reply to")
    body_text: Optional[str] = Field(default=None, description="Plain text body of the reply")
    attachment_paths: Optional[List[str]] = Field(default=None, description="List of Supabase file paths to attach")
    drive_file_ids: Optional[List[str]] = Field(default=None, description="List of Google Drive file IDs to attach")


class ReplyEmailTool(BaseGoogleTool):
    name: str = "reply_email"
    description: str = "Reply to an existing email message"
    args_schema: ArgsSchema = ReplyEmailInput

    def _run(
            self,
            message_id: str,
            config: Annotated[RunnableConfig, InjectedToolArg],
            body_text: Optional[str] = None,
            attachment_paths: Optional[List[str]] = None,
            drive_file_ids: Optional[List[str]] = None
    ) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(
            self,
            config: RunnableConfig,
            message_id: str,
            body_text: Optional[str] = None,
            attachment_paths: Optional[List[str]] = None,
            drive_file_ids: Optional[List[str]] = None
    ) -> str:
        supabase_folder = None
        drive_folder = None
        try:
            await adispatch_custom_event(
                "tool_status",
                {"text": "Sending Reply...", "icon": "↩️"}
            )
            gmail = await get_gmail_service(config)
            all_attachments = []
            if attachment_paths:
                supabase_folder, supabase_files = await download_to_disk(attachment_paths)
                all_attachments.extend(supabase_files)
            if drive_file_ids:
                drive_folder, drive_files = await _download_drive_files(config, drive_file_ids)
                all_attachments.extend(drive_files)

            reply = await gmail.reply(
                original_email=message_id,
                body_text=body_text,
                attachment_paths=all_attachments or None,
            )

            return f"Reply sent successfully. message_id: {reply.message_id}, thread_id: {reply.thread_id}"
        finally:
            if supabase_folder and supabase_folder.exists():
                shutil.rmtree(supabase_folder)
            if drive_folder and drive_folder.exists():
                shutil.rmtree(drive_folder)


class ForwardEmailInput(BaseModel):
    message_id: str = Field(description="Message ID of the email to forward")
    to: List[str] = Field(description="List of recipient email addresses to forward to")
    include_attachments: Optional[bool] = Field(default=True, description="Whether to include original attachments")


class ForwardEmailTool(BaseGoogleTool):
    name: str = "forward_email"
    description: str = "Forward an existing email message to one or more recipients"
    args_schema: ArgsSchema = ForwardEmailInput

    def _run(
            self,
            message_id: str,
            to: List[str],
            config: Annotated[RunnableConfig, InjectedToolArg],
            include_attachments: Optional[bool] = True
    ) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(
            self,
            config: RunnableConfig,
            message_id: str,
            to: List[str],
            include_attachments: Optional[bool] = True
    ) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Forwarding Email...", "icon": "⏩"}
        )
        gmail = await get_gmail_service(config)
        forward = await gmail.forward(
            original_email=message_id,
            to=to,
            include_attachments=include_attachments
        )
        return f"Email forwarded successfully. message_id: {forward.message_id}, thread_id: {forward.thread_id}"
import logging
import shutil
from typing import Optional, List, Annotated

from google.auth.exceptions import RefreshError
from googleapiclient.errors import HttpError
from langchain_core.callbacks import adispatch_custom_event
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import ArgsSchema, InjectedToolArg
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from agents.common.download_supabase_to_disk import download_to_disk
from core.auth import get_gmail_service
from core.exceptions import ProviderNotConnectedError

logger = logging.getLogger(__name__)


class WriteEmailInput(BaseModel):
    to: List[str] = Field(description="List of recipient writer addresses")
    subject: Optional[str] = Field(default=None, description="Subject line of the writer")
    body_text: Optional[str] = Field(default=None, description="Plain text body of the writer")
    cc: Optional[List[str]] = Field(default=None, description="List of CC recipient writer addresses")
    bcc: Optional[List[str]] = Field(default=None, description="List of BCC recipient writer addresses")
    attachment_paths: Optional[List[str]] = Field(default=None, description="List of file paths to attach")


class SendEmailTool(BaseTool):
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
            attachment_paths: Optional[List[str]] = None
    ) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(
            self,
            to: List[str],
            config: Annotated[RunnableConfig, InjectedToolArg],
            subject: Optional[str] = None,
            body_text: Optional[str] = None,
            cc: Optional[List[str]] = None,
            bcc: Optional[List[str]] = None,
            attachment_paths: Optional[List[str]] = None
    ) -> str:
        try:
            await adispatch_custom_event(
                "tool_status",
                {"text": "Sending Email...", "icon": "📤"}
            )
            gmail = await get_gmail_service(config)
            folder, downloaded_files = None, None
            if attachment_paths:
                folder, downloaded_files = await download_to_disk(attachment_paths)

            email = await gmail.send_email(
                to=to,
                subject=subject,
                body_text=body_text,
                cc=cc,
                bcc=bcc,
                attachment_paths=downloaded_files,
            )
            if folder: shutil.rmtree(folder)  # clean up

            return f"Email sent successfully. message_id: {email.message_id}, thread_id: {email.thread_id}"

        except (ProviderNotConnectedError, RefreshError):
            return "I currently don't have access to your gmail. Connect Gmail from the settings page."
        
        except HttpError as e:
            if e.status_code == 403:
                return "I currently don't have access to your gmail. Connect Gmail from the settings page."
            raise e

        except Exception as e:
            logger.error(f"Error in SendEmailTool: {e}", exc_info=True)
            return "Unable to send email due to internal error"


class DraftEmailTool(BaseTool):
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
            attachment_paths: Optional[List[str]] = None
    ) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(
            self,
            to: List[str],
            config: Annotated[RunnableConfig, InjectedToolArg],
            subject: Optional[str] = None,
            body_text: Optional[str] = None,
            body_html: Optional[str] = None,
            cc: Optional[List[str]] = None,
            bcc: Optional[List[str]] = None,
            attachment_paths: Optional[List[str]] = None
    ) -> str:
        try:
            await adispatch_custom_event(
                "tool_status",
                {"text": "Creating Draft...", "icon": "📝"}
            )
            gmail = await get_gmail_service(config)
            folder, downloaded_files = None, None
            if attachment_paths:
                folder, downloaded_files = await download_to_disk(attachment_paths)

            draft = await gmail.create_draft(
                to=to,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                cc=cc,
                bcc=bcc,
                attachment_paths=downloaded_files,
            )
            if folder: shutil.rmtree(folder)

            return f"Draft created successfully. message_id: {draft.message_id}, thread_id: {draft.thread_id}"

        except (ProviderNotConnectedError, RefreshError):
            return "I currently don't have access to your gmail. Connect Gmail from the settings page."
        
        except HttpError as e:
            if e.status_code == 403:
                return "I currently don't have access to your gmail. Connect Gmail from the settings page."
            raise e

        except Exception as e:
            logger.error(f"Error in DraftEmailTool: {e}", exc_info=True)
            return "Unable to create draft due to internal error"


class ReplyEmailInput(BaseModel):
    message_id: str = Field(description="message_id of the email to reply to")
    body_text: Optional[str] = Field(default=None, description="Plain text body of the reply")
    attachment_paths: Optional[List[str]] = Field(default=None, description="List of file paths to attach")


class ReplyEmailTool(BaseTool):
    name: str = "reply_email"
    description: str = "Reply to an existing writer message"
    args_schema: ArgsSchema = ReplyEmailInput

    def _run(
            self,
            message_id: str,
            config: Annotated[RunnableConfig, InjectedToolArg],
            body_text: Optional[str] = None,
            attachment_paths: Optional[List[str]] = None
    ) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(
            self,
            message_id: str,
            config: Annotated[RunnableConfig, InjectedToolArg],
            body_text: Optional[str] = None,
            attachment_paths: Optional[List[str]] = None
    ) -> str:
        try:
            await adispatch_custom_event(
                "tool_status",
                {"text": "Sending Reply...", "icon": "↩️"}
            )
            gmail = await get_gmail_service(config)
            folder, downloaded_files = None, None
            if attachment_paths:
                folder, downloaded_files = await download_to_disk(attachment_paths)

            reply = await gmail.reply(
                original_email=message_id,
                body_text=body_text,
                attachment_paths=downloaded_files,
            )
            if folder: shutil.rmtree(folder)

            return f"Reply sent successfully. message_id: {reply.message_id}, thread_id: {reply.thread_id}"

        except (ProviderNotConnectedError, RefreshError):
            return "I currently don't have access to your gmail. Connect Gmail from the settings page."
        
        except HttpError as e:
            if e.status_code == 403:
                return "I currently don't have access to your gmail. Connect Gmail from the settings page."
            raise e

        except Exception as e:
            logger.error(f"Error in ReplyEmailTool: {e}", exc_info=True)
            return "Unable to send reply due to internal error"


class ForwardEmailInput(BaseModel):
    message_id: str = Field(description="Message ID of the email to forward")
    to: List[str] = Field(description="List of recipient email addresses to forward to")
    include_attachments: Optional[bool] = Field(default=True, description="Whether to include original attachments")


class ForwardEmailTool(BaseTool):
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

    async def _arun(
            self,
            message_id: str,
            to: List[str],
            config: Annotated[RunnableConfig, InjectedToolArg],
            include_attachments: Optional[bool] = True
    ) -> str:
        try:
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

        except (ProviderNotConnectedError, RefreshError):
            return "I currently don't have access to your gmail. Connect Gmail from the settings page."
        
        except HttpError as e:
            if e.status_code == 403:
                return "I currently don't have access to your gmail. Connect Gmail from the settings page."
            raise e

        except Exception as e:
            logger.error(f"Error in ForwardEmailTool: {e}", exc_info=True)
            return "Unable to forward email due to internal error"

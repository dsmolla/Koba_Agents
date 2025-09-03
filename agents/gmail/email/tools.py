from langchain.tools import BaseTool
from google_client.services.gmail.api_service import GmailApiService
from typing import Optional, List
import os

from langchain_core.tools import ArgsSchema
from pydantic import BaseModel, Field


class SendEmailInput(BaseModel):
    """Input schema for sending emails"""
    to: List[str] = Field(description="List of recipient email addresses")
    subject: Optional[str] = Field(default=None, description="Subject line of the email")
    body_text: Optional[str] = Field(default=None, description="Plain text body of the email")
    cc: Optional[List[str]] = Field(default=None, description="List of CC recipient email addresses")
    bcc: Optional[List[str]] = Field(default=None, description="List of BCC recipient email addresses")
    attachment_paths: Optional[List[str]] = Field(default=None, description="List of file paths to attach")


class SendEmailTool(BaseTool):
    """Tool for sending emails"""

    name: str = "send_email"
    description: str  = "Send an email through Gmail to one or more recipients"
    args_schema: ArgsSchema = SendEmailInput

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(
            self,
            to: List[str],
            subject: Optional[str] = None,
            body_text: Optional[str] = None,
            cc: Optional[List[str]] = None,
            bcc: Optional[List[str]] = None,
            attachment_paths: Optional[List[str]] = None
    ) -> dict:
        """Send an email"""
        try:
            email = self.gmail_service.send_email(
                to=to,
                subject=subject,
                body_text=body_text,
                cc=cc,
                bcc=bcc,
                attachment_paths=attachment_paths,
            )
            return {
                "status": "success",
                "message_id": email.message_id,
                "thread_id": email.thread_id,
                "message": "Email sent successfully"
            }

        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Failed to send email: {str(e)}"
            }


class CreateDraftInput(BaseModel):
    """Input schema for creating email drafts"""
    to: List[str] = Field(description="List of recipient email addresses")
    subject: Optional[str] = Field(default=None, description="Subject line of the email")
    body_text: Optional[str] = Field(default=None, description="Plain text body of the email")
    body_html: Optional[str] = Field(default=None, description="HTML body of the email")
    cc: Optional[List[str]] = Field(default=None, description="List of CC recipient email addresses")
    bcc: Optional[List[str]] = Field(default=None, description="List of BCC recipient email addresses")
    attachment_paths: Optional[List[str]] = Field(default=None, description="List of file paths to attach")


class CreateDraftTool(BaseTool):
    """Tool for creating email drafts"""

    name: str = "create_email_draft"
    description: str  = "Create an email draft in Gmail"
    args_schema: ArgsSchema = CreateDraftInput

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(
            self,
            to: List[str],
            subject: Optional[str] = None,
            body_text: Optional[str] = None,
            body_html: Optional[str] = None,
            cc: Optional[List[str]] = None,
            bcc: Optional[List[str]] = None,
            attachment_paths: Optional[List[str]] = None
    ) -> dict:
        """Create an email draft"""
        try:
            draft = self.gmail_service.create_draft(
                to=to,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                cc=cc,
                bcc=bcc,
                attachment_paths=attachment_paths,
            )
            return {
                "status": "success",
                "message_id": draft.message_id,
                "thread_id": draft.thread_id,
                "message": "Draft created successfully"
            }

        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Failed to create draft: {str(e)}"
            }


class ReplyEmailInput(BaseModel):
    """Input schema for replying to emails"""
    message_id: str = Field(description="Message ID of the email to reply to")
    body_text: Optional[str] = Field(default=None, description="Plain text body of the reply")
    attachment_paths: Optional[List[str]] = Field(default=None, description="List of file paths to attach")


class ReplyEmailTool(BaseTool):
    """Tool for replying to emails"""

    name: str  = "reply_email"
    description: str  = "Reply to an existing email message"
    args_schema: ArgsSchema = ReplyEmailInput

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(
            self,
            message_id: str,
            body_text: Optional[str] = None,
            attachment_paths: Optional[List[str]] = None
    ) -> dict:
        """Reply to an email"""
        try:
            reply = self.gmail_service.reply(
                original_email=message_id,
                body_text=body_text,
                attachment_paths=attachment_paths,
            )
            return {
                "status": "success",
                "message_id": reply.message_id,
                "thread_id": reply.thread_id,
                "message": "Reply sent successfully"
            }

        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Failed to send reply: {str(e)}"
            }


class ForwardEmailInput(BaseModel):
    """Input schema for forwarding emails"""
    message_id: str = Field(description="Message ID of the email to forward")
    to: List[str] = Field(description="List of recipient email addresses to forward to")
    include_attachments: Optional[bool] = Field(default=True, description="Whether to include original attachments")


class ForwardEmailTool(BaseTool):
    """Tool for forwarding emails"""

    name: str  = "forward_email"
    description: str  = "Forward an existing email message to one or more recipients"
    args_schema: ArgsSchema = ForwardEmailInput

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(
            self,
            message_id: str,
            to: List[str],
            include_attachments: Optional[bool] = True
    ) -> dict:
        """Forward an email"""
        try:
            forward = self.gmail_service.forward(
                original_email=message_id,
                to=to,
                include_attachments=include_attachments
            )
            return {
                "status": "success",
                "message_id": forward.message_id,
                "thread_id": forward.thread_id,
                "message": "Email forwarded successfully"
            }

        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Failed to forward email: {str(e)}"
            }


class DeleteEmailInput(BaseModel):
    """Input schema for deleting emails"""
    message_id: str = Field(description="Message ID of the email to delete")


class DeleteEmailTool(BaseTool):
    """Tool for deleting emails"""

    name: str  = "delete_email"
    description: str  = "Delete an email message from Gmail. Email is moved to Trash by default"
    args_schema: ArgsSchema = DeleteEmailInput

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(self, message_id: str) -> dict:
        """Delete an email"""
        try:
            if self.gmail_service.delete_email(
                email=message_id,
                permanent=False,
            ):
                return {
                    "status": "success",
                    "message_id": message_id,
                    "message": f"Email {message_id} deleted successfully"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to delete email {message_id}"
                }

        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Failed to delete email: {str(e)}"
            }


class DownloadAttachmentInput(BaseModel):
    """Input schema for downloading email attachments"""
    message_id: str = Field(description="Message ID of the email containing the attachment")
    attachment_id: str = Field(description="ID of the attachment to download")
    filename: str = Field(description="Name of the attachment file")
    download_folder: Optional[str] = Field(default=None, description="Local path to save the attachment, defaults to Downloads/GmailAttachments")


class DownloadAttachmentTool(BaseTool):
    """Tool for downloading email attachments"""

    name: str  = "download_attachment"
    description: str  = "Download an attachment from an email message"
    args_schema: ArgsSchema = DownloadAttachmentInput

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(self, message_id: str, attachment_id: str, filename: str, download_folder: Optional[str] = None) -> dict:
        """Download an email attachment"""
        try:
            if download_folder is None:
                download_folder = os.path.join(os.path.expanduser("~"), "Downloads", "GmailAttachments")

            attachment_data = {
                "message_id": message_id,
                "attachment_id": attachment_id,
                "filename": filename
            }
            
            self.gmail_service.download_attachment(
                attachment=attachment_data,
                download_folder=download_folder
            )
            return {
                "status": "success",
                "attachment_id": attachment_id,
                "message_id": message_id,
                "message": f"{filename} successfully downloaded to {download_folder}."
            }

        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Failed to download attachment: {str(e)}"
            }



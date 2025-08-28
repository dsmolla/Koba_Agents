from langchain.tools import BaseTool
from google_client.services.gmail.api_service import GmailApiService
from textwrap import dedent
from typing import Union
import json
import os



class SendEmailTool(BaseTool):
    """Tool for sending emails"""

    name: str = "send_email"
    description: str  = dedent("""
    Send an email through Gmail to one or more recipients.
    Provide the following details:
    - to: A list of recipient email addresses (required)
    - subject: The subject line of the email (optional)
    - body_text: The plain text body of the email (optional)
    - cc: A list of CC recipient email addresses (optional)
    - bcc: A list of BCC recipient email addresses (optional)
    - attachment_paths: A list of file paths to attach to the email (optional)
    """)

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(self,tool_input: Union[str, dict]) -> dict:
        """Send an email"""
        try:
            if isinstance(tool_input, str):
                try:
                    params = json.loads(tool_input)
                except json.JSONDecodeError:
                    return {
                        "status": "error",
                        "error_type": "JSONDecodeError",
                        "error_message": "Invalid input: Please provide a valid JSON.",
                        "message": "Failed to send email: Invalid JSON input"
                    }
            else:
                params = tool_input

            email = self.gmail_service.send_email(
                to=params.get("to"),
                subject=params.get("subject"),
                body_text=params.get("body_text"),
                cc=params.get("cc"),
                bcc=params.get("bcc"),
                attachment_paths=params.get("attachment_paths"),
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


class CreateDraftTool(BaseTool):
    """Tool for creating email drafts"""

    name: str = "create_email_draft"
    description: str  = dedent("""
    Create an email draft in Gmail.
    Provide the following details:
    - to: A list of recipient email addresses (required)
    - subject: The subject line of the email (optional)
    - body_text: The plain text body of the email (optional)
    - body_html: The HTML body of the email (optional)
    - cc: A list of CC recipient email addresses (optional)
    - bcc: A list of BCC recipient email addresses (optional)
    - attachment_paths: A list of file paths to attach to the draft (optional)
    """)

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(self, tool_input: Union[str, dict]) -> dict:
        """Create an email draft"""
        try:
            if isinstance(tool_input, str):
                try:
                    params = json.loads(tool_input)
                except json.JSONDecodeError:
                    return {
                        "status": "error",
                        "error_type": "JSONDecodeError",
                        "error_message": "Invalid input: Please provide a valid JSON.",
                        "message": "Failed to create draft: Invalid JSON input"
                    }
            else:
                params = tool_input
            draft = self.gmail_service.create_draft(
                to=params.get("to"),
                subject=params.get("subject"),
                body_text=params.get("body_text"),
                body_html=params.get("body_html"),
                cc=params.get("cc"),
                bcc=params.get("bcc"),
                attachment_paths=params.get("attachment_paths"),
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


class ReplyEmailTool(BaseTool):
    """Tool for replying to emails"""

    name: str  = "reply_email"
    description: str  = dedent("""
    Reply to an existing email message.
    Provide the following details:
    - message_id: The Message ID of the email to reply to (required)
    - body_text: The plain text body of your reply (optional)
    - attachment_paths: A list of file paths to attach to your reply (optional)
    """)

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(self, tool_input: Union[str, dict]) -> dict:
        """Reply to an email"""
        try:
            if isinstance(tool_input, str):
                try:
                    params = json.loads(tool_input)
                except json.JSONDecodeError:
                    return {
                        "status": "error",
                        "error_type": "JSONDecodeError",
                        "error_message": "Invalid input: Please provide a valid JSON.",
                        "message": "Failed to send reply: Invalid JSON input"
                    }
            else:
                params = tool_input
            reply = self.gmail_service.reply(
                original_email=params.get("message_id"),
                body_text=params.get("body_text"),
                attachment_paths=params.get("attachment_paths"),
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


class ForwardEmailTool(BaseTool):
    """Tool for forwarding emails"""

    name: str  = "forward_email"
    description: str  = dedent("""
    Forward an existing email message to one or more recipients.
    Provide the following details:
    - message_id: The Message ID of the email to forward (required)
    - to: A list of recipient email addresses to forward the email to (required)
    - include_attachments: Boolean to indicate whether to include original attachments (default is True)
    """)

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(self, tool_input: Union[str, dict]) -> dict:
        """Forward an email"""
        try:
            if isinstance(tool_input, str):
                try:
                    params = json.loads(tool_input)
                except json.JSONDecodeError:
                    return {
                        "status": "error",
                        "error_type": "JSONDecodeError",
                        "error_message": "Invalid input: Please provide a valid JSON.",
                        "message": "Failed to forward email: Invalid JSON input"
                    }
            else:
                params = tool_input
            forward = self.gmail_service.forward(
                original_email=params.get("message_id"),
                to=params.get("to"),
                include_attachments=params.get("include_attachments", True)
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


class DeleteEmailTool(BaseTool):
    """Tool for deleting emails"""

    name: str  = "delete_email"
    description: str  = dedent("""
    Delete an email message from Gmail. Email is moved to Trash by default.
    Provide the following details:
    - message_id: The message ID of the email to delete (required)
    """)

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(self, tool_input: Union[str, dict]) -> dict:
        """Delete an email"""
        try:
            if isinstance(tool_input, str):
                try:
                    params = json.loads(tool_input)
                except json.JSONDecodeError:
                    return {
                        "status": "error",
                        "error_type": "JSONDecodeError",
                        "error_message": "Invalid input: Please provide a valid JSON.",
                        "message": "Failed to delete email: Invalid JSON input"
                    }
            else:
                params = tool_input
            if self.gmail_service.delete_email(
                email=params.get("message_id"),
                permanent=False,
            ):
                return {
                    "status": "success",
                    "message_id": params.get("message_id"),
                    "message": f"Email {params.get('message_id')} deleted successfully"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to delete email {params.get('message_id')}"
                }

        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Failed to delete email: {str(e)}"
            }


class DownloadAttachmentTool(BaseTool):
    """Tool for downloading email attachments"""

    name: str  = "download_attachment"
    description: str  = dedent("""
    Download an attachment from an email message.
    Provide the following details:
    - message_id: The Message ID of the email containing the attachment (required)
    - attachment_id: The ID of the attachment to download (required)
    - filename: The name of the attachment file (required)
    - download_folder: The local file path to save the downloaded attachment (optional, defaults to Downloads/GmailAttachments)
    """)

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(self, tool_input: Union[str, dict]) -> dict:
        """Download an email attachment"""
        try:
            if isinstance(tool_input, str):
                try:
                    params = json.loads(tool_input)
                except json.JSONDecodeError:
                    return {
                        "status": "error",
                        "error_type": "JSONDecodeError",
                        "error_message": "Invalid input: Please provide a valid JSON.",
                        "message": "Failed to download attachment: Invalid JSON input"
                    }
            else:
                params = tool_input

            self.gmail_service.download_attachment(
                attachment=tool_input,
                download_folder=params.get("download_folder", os.path.join(os.path.expanduser("~"), "Downloads", "GmailAttachments"))
            )
            return {
                "status": "success",
                "attachment_id": params.get("attachment_id"),
                "message_id": params.get("message_id"),
                "message": f"{params.get("filename")} successfully downloaded to {params.get('download_folder')}."
            }

        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Failed to download attachment: {str(e)}"
            }



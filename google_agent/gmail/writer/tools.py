from typing import Optional, List

from google_client.services.gmail.api_service import GmailApiService
from langchain.tools import BaseTool
from langchain_core.tools import ArgsSchema
from pydantic import BaseModel, Field

from google_agent.shared.exceptions import ToolException
from google_agent.shared.response import ToolResponse


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

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService, ):
        super().__init__(gmail_service=gmail_service)

    def _run(
            self,
            to: List[str],
            subject: Optional[str] = None,
            body_text: Optional[str] = None,
            cc: Optional[List[str]] = None,
            bcc: Optional[List[str]] = None,
            attachment_paths: Optional[List[str]] = None
    ) -> ToolResponse:
        try:

            print(attachment_paths)

            email = self.gmail_service.send_email(
                to=to,
                subject=subject,
                body_text=body_text,
                cc=cc,
                bcc=bcc,
                attachment_paths=attachment_paths,
            )
            return ToolResponse(
                status="success",
                message=f"Email sent successfully. message_id: {email.message_id}, thread_id: {email.thread_id}",
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to send writer: {e}"
            )


class DraftEmailTool(BaseTool):
    name: str = "draft_email"
    description: str = "Create an email draft in Gmail"
    args_schema: ArgsSchema = WriteEmailInput

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService, ):
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
    ) -> ToolResponse:
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
            return ToolResponse(
                status="success",
                message=f"Draft created successfully. message_id: {draft.message_id}, thread_id: {draft.thread_id}",
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to create draft: {e}",
            )


class ReplyEmailInput(BaseModel):
    message_id: str = Field(description="message_id of the email to reply to")
    body_text: Optional[str] = Field(default=None, description="Plain text body of the reply")
    attachment_paths: Optional[List[str]] = Field(default=None, description="List of file paths to attach")


class ReplyEmailTool(BaseTool):
    name: str = "reply_email"
    description: str = "Reply to an existing writer message"
    args_schema: ArgsSchema = ReplyEmailInput

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService, ):
        super().__init__(gmail_service=gmail_service)

    def _run(
            self,
            message_id: str,
            body_text: Optional[str] = None,
            attachment_paths: Optional[List[str]] = None
    ) -> ToolResponse:
        try:

            reply = self.gmail_service.reply(
                original_email=message_id,
                body_text=body_text,
                attachment_paths=attachment_paths,
            )
            return ToolResponse(
                status="success",
                message=f"Reply sent successfully. message_id: {reply.message_id}, thread_id: {reply.thread_id}",
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to send reply: {e}"
            )


class ForwardEmailInput(BaseModel):
    message_id: str = Field(description="Message ID of the email to forward")
    to: List[str] = Field(description="List of recipient email addresses to forward to")
    include_attachments: Optional[bool] = Field(default=True, description="Whether to include original attachments")


class ForwardEmailTool(BaseTool):
    name: str = "forward_email"
    description: str = "Forward an existing email message to one or more recipients"
    args_schema: ArgsSchema = ForwardEmailInput

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService, ):
        super().__init__(gmail_service=gmail_service)

    def _run(
            self,
            message_id: str,
            to: List[str],
            include_attachments: Optional[bool] = True
    ) -> ToolResponse:
        try:
            forward = self.gmail_service.forward(
                original_email=message_id,
                to=to,
                include_attachments=include_attachments
            )
            return ToolResponse(
                status="success",
                message=f"Email forwarded successfully. message_id: {forward.message_id}, thread_id: {forward.thread_id}",
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to forward writer: {e}"
            )

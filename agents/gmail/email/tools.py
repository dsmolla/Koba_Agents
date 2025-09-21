from datetime import datetime

from google_client.services.gmail import EmailQueryBuilder
from langchain.tools import BaseTool
from google_client.services.gmail.api_service import GmailApiService
from typing import Optional, List, Union, Callable
import os

from langchain_core.tools import ArgsSchema
from pydantic import BaseModel, Field

from shared.exceptions import ToolException


class GetEmailInput(BaseModel):
    """Input schema for getting full email details"""
    message_id: str = Field(description="The message_id of the email to retrieve")
    get_body_text: Optional[bool] = Field(default=False, description="Include body text in full return type")
    get_attachments: Optional[bool] = Field(default=False, description="Include attachment metadata in response")


class GetEmailTool(BaseTool):
    """Tool for retrieving full email details"""
    
    name: str = "get_full_email"
    description: str = "Retrieve full email detail from Gmail by message ID"
    args_schema: ArgsSchema = GetEmailInput

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService, ):
        super().__init__(gmail_service=gmail_service)

    def _run(self, message_id: str, get_body_text: bool = False, get_attachments: bool = False) -> dict:
        """Retrieve full email detail"""
        try:
            email = self.gmail_service.get_email(message_id=message_id)
            return_dict = {
                "status": "success"
            }
            email_dict = email.to_dict()
            if not get_body_text:
                del email_dict['body']
            if not get_attachments:
                del email_dict['attachments']

            return return_dict | email_dict
            
        except Exception as e:
            raise ToolException(
                message=f"Failed to fetch email: {str(e)}",
                tool_name=self.name
            )


class SearchEmailsInput(BaseModel):
    """Input schema for querying emails"""
    include_attachments: Optional[bool] = Field(default=False, description="Include attachment metadata in response")
    include_promotions: Optional[bool] = Field(default=False, description="Include emails from Promotions category")
    limit: Optional[int] = Field(default=50, description="Maximum number of emails to retrieve")
    search: Optional[str] = Field(default=None, description="Search thread to filter emails")
    from_sender: Optional[str] = Field(default=None, description="Filter emails from specific sender")
    to_recipient: Optional[str] = Field(default=None, description="Filter emails to specific recipient")
    with_subject: Optional[str] = Field(default=None, description="Filter emails with specific subject")
    with_attachments: Optional[bool] = Field(default=None, description="Filter emails that have attachments")
    is_read: Optional[bool] = Field(default=None, description="Filter read emails")
    is_unread: Optional[bool] = Field(default=None, description="Filter unread emails")
    is_starred: Optional[bool] = Field(default=None, description="Filter starred emails")
    is_important: Optional[bool] = Field(default=None, description="Filter important emails")
    in_folder: Optional[str] = Field(default=None, description="Filter emails in specific folder")
    with_label: Optional[str] = Field(default=None, description="Filter emails with specific label")
    today: Optional[bool] = Field(default=None, description="Filter emails from today")
    yesterday: Optional[bool] = Field(default=None, description="Filter emails from yesterday")
    last_days: Optional[int] = Field(default=None, description="Filter emails from last N days")
    this_week: Optional[bool] = Field(default=None, description="Filter emails from this week")
    this_month: Optional[bool] = Field(default=None, description="Filter emails from this month")
    after_date: Optional[str] = Field(default=None, description="Filter emails after date (YYYY-MM-DD)")
    before_date: Optional[str] = Field(default=None, description="Filter emails before date (YYYY-MM-DD)")
    get_body_text: Optional[bool] = Field(default=True, description="Include body text in full return type")


class SearchEmailsTool(BaseTool):
    """Tool for querying emails"""

    name: str = "search_emails"
    description: str = "Query and retrieve emails from Gmail based on various filters."
    args_schema: ArgsSchema = SearchEmailsInput

    gmail_service: GmailApiService
    

    def __init__(self, gmail_service: GmailApiService, ):
        super().__init__(gmail_service=gmail_service)

    def build_query(self, params: dict) -> EmailQueryBuilder:
        query_builder = self.gmail_service.query()
        if params.get("include_promotions") is not True:
            query_builder = query_builder.without_label('Promotions')
        if params.get("limit") is not None:
            query_builder = query_builder.limit(params.get("limit"))
        if params.get("search") is not None:
            query_builder = query_builder.search(params.get("search"))
        if params.get("from_sender") is not None:
            query_builder = query_builder.from_sender(params.get("from_sender"))
        if params.get("to_recipient") is not None:
            query_builder = query_builder.to_recipient(params.get("to_recipient"))
        if params.get("with_subject") is not None:
            query_builder = query_builder.with_subject(params.get("with_subject"))
        if params.get("with_attachments") is True:
            query_builder = query_builder.with_attachments()
        if params.get("is_read") is True:
            query_builder = query_builder.is_read()
        if params.get("is_unread") is not None:
            query_builder = query_builder.is_unread()
        if params.get("is_starred") is not None:
            query_builder = query_builder.is_starred()
        if params.get("is_important") is True:
            query_builder = query_builder.is_important()
        if params.get("in_folder") is not None:
            query_builder = query_builder.in_folder(params.get("in_folder"))
        if params.get("with_label") is not None:
            query_builder = query_builder.with_label(params.get("with_label"))
        if params.get("today") is True:
            query_builder = query_builder.today()
        if params.get("yesterday") is True:
            query_builder = query_builder.yesterday()
        if params.get("last_days") is not None:
            query_builder = query_builder.last_days(params.get("last_days"))
        if params.get("this_week") is True:
            query_builder = query_builder.this_week()
        if params.get("this_month") is True:
            query_builder = query_builder.this_month()
        if params.get("after_date") is not None:
            after_date = datetime.strptime(params.get("after_date"), "%Y-%m-%d")
            query_builder = query_builder.after_date(after_date)
        if params.get("before_date") is not None:
            before_date = datetime.strptime(params.get("before_date"), "%Y-%m-%d")
            query_builder = query_builder.before_date(before_date)

        return query_builder

    def _run(
            self,
            include_attachments: Optional[bool] = False,
            include_promotions: Optional[bool] = False,
            limit: Optional[int] = 50,
            search: Optional[str] = None,
            from_sender: Optional[str] = None,
            to_recipient: Optional[str] = None,
            with_subject: Optional[str] = None,
            with_attachments: Optional[bool] = None,
            is_read: Optional[bool] = None,
            is_unread: Optional[bool] = None,
            is_starred: Optional[bool] = None,
            is_important: Optional[bool] = None,
            in_folder: Optional[str] = None,
            with_label: Optional[str] = None,
            today: Optional[bool] = None,
            yesterday: Optional[bool] = None,
            last_days: Optional[int] = None,
            this_week: Optional[bool] = None,
            this_month: Optional[bool] = None,
            after_date: Optional[str] = None,
            before_date: Optional[str] = None,
            get_body_text: Optional[bool] = False
    ) -> Union[dict, List[dict]]:
        """Query and retrieve emails based on filters"""
        try:
            
            params = {
                "include_promotions": include_promotions,
                "limit": limit,
                "search": search,
                "from_sender": from_sender,
                "to_recipient": to_recipient,
                "with_subject": with_subject,
                "with_attachments": with_attachments,
                "is_read": is_read,
                "is_unread": is_unread,
                "is_starred": is_starred,
                "is_important": is_important,
                "in_folder": in_folder,
                "with_label": with_label,
                "today": today,
                "yesterday": yesterday,
                "last_days": last_days,
                "this_week": this_week,
                "this_month": this_month,
                "after_date": after_date,
                "before_date": before_date
            }

            query = self.build_query(params)
            emails = query.execute()

            return [{
                "message_id": email.message_id,
                "thread_id": email.thread_id,
                "subject": email.subject,
                "from": email.sender,
                "to": email.recipients,
                "date_time": email.date_time.isoformat(),
                "snippet": email.snippet,
                "is_read": email.is_read,
                "is_starred": email.is_starred,
                "is_important": email.is_important,
                "labels": email.labels,
                "has_attachments": email.has_attachments(),
                "body_text": email.get_plain_text_content() if get_body_text else None,
            }
                for email in emails
            ]


        except Exception as e:
            raise ToolException(
                message=f"Failed to search emails: {str(e)}",
                tool_name=self.name
            )


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
            raise ToolException(
                message=f"Failed to send email: {str(e)}",
                tool_name=self.name
            )


class DraftEmailInput(BaseModel):
    """Input schema for creating email drafts"""
    to: List[str] = Field(description="List of recipient email addresses")
    subject: Optional[str] = Field(default=None, description="Subject line of the email")
    body_text: Optional[str] = Field(default=None, description="Plain text body of the email")
    body_html: Optional[str] = Field(default=None, description="HTML body of the email")
    cc: Optional[List[str]] = Field(default=None, description="List of CC recipient email addresses")
    bcc: Optional[List[str]] = Field(default=None, description="List of BCC recipient email addresses")
    attachment_paths: Optional[List[str]] = Field(default=None, description="List of file paths to attach")


class DraftEmailTool(BaseTool):
    """Tool for creating email drafts"""

    name: str = "draft_email"
    description: str  = "Create an email draft in Gmail"
    args_schema: ArgsSchema = DraftEmailInput

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
            raise ToolException(
                message=f"Failed to create draft: {str(e)}",
                tool_name=self.name
            )


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
    

    def __init__(self, gmail_service: GmailApiService, ):
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
            raise ToolException(
                message=f"Failed to send reply: {str(e)}",
                tool_name=self.name
            )


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
    

    def __init__(self, gmail_service: GmailApiService, ):
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
            raise ToolException(
                message=f"Failed to forward email: {str(e)}",
                tool_name=self.name
            )


class DeleteEmailInput(BaseModel):
    """Input schema for deleting emails"""
    message_id: str = Field(description="Message ID of the email to delete")


class DeleteEmailTool(BaseTool):
    """Tool for deleting emails"""

    name: str  = "delete_email"
    description: str  = "Delete an email message from Gmail. Email is moved to Trash by default"
    args_schema: ArgsSchema = DeleteEmailInput

    gmail_service: GmailApiService
    

    def __init__(self, gmail_service: GmailApiService, ):
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
            raise ToolException(
                message=f"Failed to delete email: {str(e)}",
                tool_name=self.name
            )


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
    

    def __init__(self, gmail_service: GmailApiService, ):
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
            raise ToolException(
                message=f"Failed to download attachment: {str(e)}",
                tool_name=self.name
            )


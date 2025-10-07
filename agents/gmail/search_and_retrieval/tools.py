import json
import os
from datetime import datetime
from typing import Optional

from google_client.services.gmail import EmailQueryBuilder
from google_client.services.gmail.api_service import GmailApiService
from langchain.tools import BaseTool
from langchain_core.tools import ArgsSchema
from pydantic import BaseModel, Field

from agents.gmail.shared.email_cache import EmailCache
from shared.exceptions import ToolException
from shared.response import ToolResponse


class GetEmailInput(BaseModel):
    message_id: str = Field(description="The message_id of the email to retrieve")


class GetEmailTool(BaseTool):
    name: str = "get_email"
    description: str = "Get email from Gmail by message_id"
    args_schema: ArgsSchema = GetEmailInput

    gmail_service: GmailApiService
    email_cache: EmailCache

    def __init__(self, gmail_service: GmailApiService, email_cache: EmailCache):
        super().__init__(gmail_service=gmail_service, email_cache=email_cache)

    def _run(self, message_id: str) -> ToolResponse:
        try:
            email = self.email_cache.retrieve(message_id)
            if email is None:
                email = self.email_cache.save(
                    self.gmail_service.get_email(message_id=message_id)
                )

            return ToolResponse(
                status="success",
                message=json.dumps(email),
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to fetch email: {e}"
            )


class GetThreadDetailsInput(BaseModel):
    thread_id: str = Field(description="The ID of the thread to retrieve details for")


class GetThreadDetailsTool(BaseTool):
    name: str = "get_thread_details"
    description: str = "Get detailed information about a specific writer thread including all messages"
    args_schema: ArgsSchema = GetThreadDetailsInput

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService, ):
        super().__init__(gmail_service=gmail_service)

    def _run(self, thread_id: str) -> dict:
        """Get detailed information about a specific thread"""
        try:

            thread = self.gmail_service.get_thread(thread_id)

            return {
                "status": "success",
                "thread_id": thread.thread_id,
                "message_count": len(thread.messages),
                "unread_count": thread.get_unread_count(),
                "has_unread": thread.has_unread_messages(),
                "participants": [participant.to_dict() for participant in thread.get_participants()],
                "messages": [
                    {
                        "message_id": msg.message_id,
                        "subject": msg.subject,
                        "from": msg.sender,
                        "to": msg.recipients,
                        "date_time": msg.date_time.isoformat() if msg.date_time else None,
                        "snippet": msg.snippet,
                        "body": msg.get_plain_text_content(),
                        "is_read": msg.is_read,
                        "is_starred": msg.is_starred,
                        "is_important": msg.is_important,
                        "organization": msg.labels,
                        "has_attachments": msg.has_attachments()
                    }
                    for msg in thread.messages
                ]
            }

        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Error getting thread details: {str(e)}"
            }


class SearchEmailsInput(BaseModel):
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


class SearchEmailsTool(BaseTool):
    name: str = "search_emails"
    description: str = "search and retrieve emails from Gmail based on various filters. Returns email snippets"
    args_schema: ArgsSchema = SearchEmailsInput

    gmail_service: GmailApiService
    email_cache: EmailCache

    def __init__(self, gmail_service: GmailApiService, email_cache: EmailCache):
        super().__init__(gmail_service=gmail_service, email_cache=email_cache)

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
            before_date: Optional[str] = None
    ) -> ToolResponse:
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

            result = []

            for email in emails:
                email_temp = self.email_cache.save(email).copy()
                # drop body and attachments to only return snippet
                del email_temp['body']
                del email_temp['attachments']
                result.append(email_temp)

            return ToolResponse(
                status="success",
                message=json.dumps(result),
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to search emails: {e}"
            )


class DownloadAttachmentInput(BaseModel):
    message_id: str = Field(description="Message ID of the writer containing the attachment")
    attachment_id: Optional[str] = Field(default=None,
                                         description="ID of the attachment to download. Leave empty to download all attachments in the email")
    download_folder: Optional[str] = Field(default=None,
                                           description="Local path to save the attachment, defaults to Downloads/GmailAttachments")


class DownloadAttachmentTool(BaseTool):
    name: str = "download_attachment"
    description: str = "Download an attachment from an email message"
    args_schema: ArgsSchema = DownloadAttachmentInput

    gmail_service: GmailApiService
    email_cache: EmailCache

    def __init__(self, gmail_service: GmailApiService, email_cache: EmailCache):
        super().__init__(gmail_service=gmail_service, email_cache=email_cache)

    def _run(self, message_id: str, attachment_id: Optional[str] = None,
             download_folder: Optional[str] = None) -> ToolResponse:
        try:
            download_folder = os.path.join(os.path.expanduser("~"), "Downloads", "GmailAttachments")

            email = self.email_cache.retrieve(message_id)
            if email is None:
                email = self.email_cache.save(
                    self.gmail_service.get_email(message_id),
                )

            attachments_downloaded = []
            if attachment_id is None:
                for attachment in email["attachments"]:
                    attachment_data = {
                        "message_id": message_id,
                        "attachment_id": attachment["attachment_id"],
                        "filename": attachment["filename"],
                    }

                    downloaded_path = self.gmail_service.download_attachment(
                        attachment=attachment_data,
                        download_folder=download_folder
                    )
                    attachments_downloaded.append(downloaded_path)

            else:
                filename = ""
                for attachment in email["attachments"]:
                    if attachment["attachment_id"] == attachment_id:
                        filename = attachment["filename"]
                        break

                attachment_data = {
                    "message_id": message_id,
                    "attachment_id": attachment_id,
                    "filename": filename,
                }

                downloaded_path = self.gmail_service.download_attachment(
                    attachment=attachment_data,
                    download_folder=download_folder
                )
                attachments_downloaded.append(downloaded_path)

            return ToolResponse(
                status="success",
                message=f"Downloaded attachments: {', '.join(attachments_downloaded)}",
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to download attachment: {e}"
            )


class ListUserLabelsTool(BaseTool):
    name: str = "list_user_labels"
    description: str = "List all user-created labels in Gmail. It does not include system organization like INBOX, SENT, SPAM, etc."

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(self) -> ToolResponse:
        try:
            labels = self.gmail_service.list_labels()
            user_labels = [label for label in labels if label.type == "user"]
            user_labels = [{
                "label_id": label.id,
                "name": label.name
            } for label in user_labels
            ]
            return ToolResponse(
                status="success",
                message=json.dumps(user_labels),
            )
        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to list user labels: {e}"
            )

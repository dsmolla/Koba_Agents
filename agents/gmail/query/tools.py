from datetime import datetime
from typing import Union, Optional, List

from google_client.services.gmail import EmailQueryBuilder
from langchain.tools.base import BaseTool
from google_client.services.gmail.api_service import GmailApiService
from langchain_core.tools import ArgsSchema
from pydantic import BaseModel, Field


def build_query(gmail_service: GmailApiService, params: dict) -> EmailQueryBuilder:
    query_builder = gmail_service.query()
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


class ListEmailsInput(BaseModel):
    """Input schema for querying emails"""
    return_type: Optional[str] = Field(default="metadata", description="Level of detail: 'metadata' or 'full'")
    include_attachments: Optional[bool] = Field(default=False, description="Include attachment metadata in response")
    include_promotions: Optional[bool] = Field(default=False, description="Include emails from Promotions category")
    limit: Optional[int] = Field(default=50, description="Maximum number of emails to retrieve")
    search: Optional[str] = Field(default=None, description="Search query to filter emails")
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


class QueryEmailsTool(BaseTool):
    """Tool for querying emails"""

    name: str  = "list_emails"
    description: str  = "Query and retrieve emails from Gmail based on various filters."
    args_schema: ArgsSchema = ListEmailsInput

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(
            self,
            return_type: Optional[str] = "metadata",
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

            query = build_query(self.gmail_service, params)
            emails = query.execute()

            if return_type == "metadata":
                return [{
                    "message_id": email.message_id,
                    "subject": email.subject,
                    "from": email.sender,
                    "to": email.recipients,
                    "date_time": email.date_time.isoformat(),
                    "snippet": email.snippet,
                    "is_read": email.is_read,
                    "is_starred": email.is_starred,
                    "is_important": email.is_important,
                    "labels": email.labels,
                    "has_attachments": email.has_attachments()
                }
                    for email in emails
                ]
            else:  # full
                return [{
                    "message_id": email.message_id,
                    "subject": email.subject,
                    "from": email.sender,
                    "to": email.recipients,
                    "date_time": email.date_time.isoformat(),
                    "snippet": email.snippet,
                    "body_text": email.body_text,
                    "is_read": email.is_read,
                    "is_starred": email.is_starred,
                    "is_important": email.is_important,
                    "labels": email.labels,
                    "attachments": [attachment.to_dict() for attachment in email.attachments] if include_attachments else None
                }
                    for email in emails
                ]

        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Error querying emails: {str(e)}"
            }


class ListThreadsInput(BaseModel):
    """Input schema for querying email threads"""
    limit: Optional[int] = Field(default=50, description="Maximum number of threads to retrieve")
    search: Optional[str] = Field(default=None, description="Search query to filter threads")
    from_sender: Optional[str] = Field(default=None, description="Filter threads from specific sender")
    to_recipient: Optional[str] = Field(default=None, description="Filter threads to specific recipient")
    with_subject: Optional[str] = Field(default=None, description="Filter threads with specific subject")
    with_attachments: Optional[bool] = Field(default=None, description="Filter threads with attachments")
    is_read: Optional[bool] = Field(default=None, description="Filter threads with read emails")
    is_unread: Optional[bool] = Field(default=None, description="Filter threads with unread emails")
    is_starred: Optional[bool] = Field(default=None, description="Filter threads with starred emails")
    is_important: Optional[bool] = Field(default=None, description="Filter threads with important emails")
    in_folder: Optional[str] = Field(default=None, description="Filter threads in specific folder")
    with_label: Optional[str] = Field(default=None, description="Filter threads with specific label")
    today: Optional[bool] = Field(default=None, description="Filter threads from today")
    yesterday: Optional[bool] = Field(default=None, description="Filter threads from yesterday")
    last_days: Optional[int] = Field(default=None, description="Filter threads from last N days")
    this_week: Optional[bool] = Field(default=None, description="Filter threads from this week")
    this_month: Optional[bool] = Field(default=None, description="Filter threads from this month")
    after_date: Optional[str] = Field(default=None, description="Filter threads after date (YYYY-MM-DD)")
    before_date: Optional[str] = Field(default=None, description="Filter threads before date (YYYY-MM-DD)")


class QueryThreadsTool(BaseTool):
    """Tool for querying email threads"""

    name: str  = "list_threads"
    description: str  = "Query and retrieve email threads from Gmail based on various filters"
    args_schema: ArgsSchema = ListThreadsInput

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(
            self,
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
    ) -> Union[dict, List[dict]]:
        """Query and retrieve email threads based on filters"""
        try:
            params = {
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

            query = build_query(self.gmail_service, params)
            threads = query.get_threads()

            return [{
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
                        "is_read": msg.is_read,
                        "is_starred": msg.is_starred,
                        "is_important": msg.is_important,
                        "labels": msg.labels,
                        "has_attachments": msg.has_attachments()
                    }
                    for msg in thread.messages
                ],
            }
                for thread in threads
            ]

        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Error querying threads: {str(e)}"
            }



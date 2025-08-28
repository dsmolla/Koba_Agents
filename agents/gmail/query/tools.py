import json
from datetime import datetime
from textwrap import dedent
from typing import Union

from google_client.services.gmail import EmailQueryBuilder
from langchain.tools.base import BaseTool
from google_client.services.gmail.api_service import GmailApiService


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


class QueryEmailsTool(BaseTool):
    """Tool for querying emails"""

    name: str  = "list_emails"
    description: str  = dedent("""
    Query and retrieve emails from Gmail based on various filters.
    You can filter emails using the following parameters:
    - return_type: "metadata" (default) or "full" to specify the level of detail in the returned emails.
                    "metadata" returns message_id, subject, from, to, snippet, date_time, labels and has_attachments.
                    "full" returns all metadata plus body_text and attachments metadata (if any).
    - include_attachments: Boolean to include attachment metadata in the response (only applicable if return_type is "full")
    - include_promotions: Boolean to include emails from the "Promotions" category (default is False)
    - limit: Maximum number of emails to retrieve (default is 50, max is 250)
    - search: Search query to filter emails
    - from_sender: Filter emails from a specific sender email address
    - to_recipient: Filter emails sent to a specific recipient email address
    - with_subject: Filter emails with a specific subject
    - with_attachments: Boolean to filter emails that have attachments
    - is_read: Boolean to filter read emails
    - is_unread: Boolean to filter unread emails
    - is_starred: Boolean to filter starred emails
    - is_important: Boolean to filter important emails
    - in_folder: Filter emails in a specific folder (e.g., "INBOX", "SENT")
    - with_label: Filter emails with a specific label
    - today: Boolean to filter emails from today
    - yesterday: Boolean to filter emails from yesterday
    - last_days: Filter emails from the last N days
    - this_week: Boolean to filter emails from this week
    - this_month: Boolean to filter emails from this month
    - after_date: Filter emails after a specific date (format: YYYY-MM-DD)
    - before_date: Filter emails before a specific date (format: YYYY-MM-DD)    
    """)

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(self, tool_input: Union[str, dict]) -> [list[dict]]:
        """Query and retrieve emails based on filters"""
        try:
            if isinstance(tool_input, str):
                try:
                    params = json.loads(tool_input)
                except json.JSONDecodeError:
                    return {
                        "status": "error",
                        "error_type": "JSONDecodeError",
                        "error_message": "Invalid JSON input",
                        "message": "Invalid input: Please provide a valid JSON."
                    }
            else:
                params = tool_input

            query = build_query(self.gmail_service, params)
            emails = query.execute()

            if params.get("return_type", "metadata") == "metadata":
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
                    "body_text": email.body_text if params.get("get_body_text", True) else None,
                    "is_read": email.is_read,
                    "is_starred": email.is_starred,
                    "is_important": email.is_important,
                    "labels": email.labels,
                    "attachments": [attachment.to_dict() for attachment in email.attachments] if params.get("include_attachments", False) else None
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


class QueryThreadsTool(BaseTool):
    """Tool for querying email threads"""

    name: str  = "list_threads"
    description: str  = dedent("""
    Query and retrieve email threads from Gmail based on various filters.
    You can filter threads using the following parameters:
    - limit: Maximum number of threads to retrieve (default is 50, max is 250)
    - search: Search query to filter threads
    - from_sender: Filter threads with emails from a specific sender email address
    - to_recipient: Filter threads with emails sent to a specific recipient email address
    - with_subject: Filter threads with emails that have a specific subject
    - with_attachments: Boolean to filter threads that have emails with attachments
    - is_read: Boolean to filter threads with read emails
    - is_unread: Boolean to filter threads with unread emails
    - is_starred: Boolean to filter threads with starred emails
    - is_important: Boolean to filter threads with important emails
    - in_folder: Filter threads in a specific folder (e.g., "INBOX", "SENT")
    - with_label: Filter threads with a specific label
    - today: Boolean to filter threads with emails from today
    - yesterday: Boolean to filter threads with emails from yesterday
    - last_days: Filter threads with emails from the last N days
    - this_week: Boolean to filter threads with emails from this week
    - this_month: Boolean to filter threads with emails from this month
    - after_date: Filter threads with emails after a specific date (format: YYYY-MM-DD)
    - before_date: Filter threads with emails before a specific date (format: YYYY-MM-DD)    
    """)

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(self, tool_input: Union[str, dict]) -> [list[dict]]:
        """Query and retrieve email threads based on filters"""
        try:
            if isinstance(tool_input, str):
                try:
                    params = json.loads(tool_input)
                except json.JSONDecodeError:
                    return {
                        "status": "error",
                        "error_type": "JSONDecodeError",
                        "error_message": "Invalid JSON input",
                        "message": "Invalid input: Please provide a valid JSON."
                    }
            else:
                params = tool_input

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



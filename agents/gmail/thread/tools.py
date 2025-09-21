from typing import Union, Optional, List, Callable

from google_client.services.gmail import EmailQueryBuilder
from langchain.tools.base import BaseTool
from google_client.services.gmail.api_service import GmailApiService
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import ArgsSchema
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from shared.constants import MODELS


class SearchThreadsInput(BaseModel):
    """Input schema for querying email threads"""
    limit: Optional[int] = Field(default=50, description="Maximum number of threads to retrieve")
    search: Optional[str] = Field(default=None, description="Search thread to filter threads")
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


class SearchThreadsTool(BaseTool):
    """Tool for querying email threads"""

    name: str  = "search_threads"
    description: str  = "Query and retrieve email threads from Gmail based on various filters"
    args_schema: ArgsSchema = SearchThreadsInput

    gmail_service: GmailApiService
    

    def __init__(self, gmail_service: GmailApiService, ):
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

            query = self._build_query(params)
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

    def _build_query(self, params: dict) -> EmailQueryBuilder:
        """Build email query with provided parameters"""
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
        if params.get("with_attachments") is not None and params.get("with_attachments"):
            query_builder = query_builder.with_attachments()
        if params.get("is_read") is not None and params.get("is_read"):
            query_builder = query_builder.is_read()
        if params.get("is_unread") is not None and params.get("is_unread"):
            query_builder = query_builder.is_unread()
        if params.get("is_starred") is not None and params.get("is_starred"):
            query_builder = query_builder.is_starred()
        if params.get("is_important") is not None and params.get("is_important"):
            query_builder = query_builder.is_important()
        if params.get("in_folder") is not None:
            query_builder = query_builder.in_folder(params.get("in_folder"))
        if params.get("with_label") is not None:
            query_builder = query_builder.with_label(params.get("with_label"))
        if params.get("today") is not None and params.get("today"):
            query_builder = query_builder.today()
        if params.get("yesterday") is not None and params.get("yesterday"):
            query_builder = query_builder.yesterday()
        if params.get("last_days") is not None:
            query_builder = query_builder.last_days(params.get("last_days"))
        if params.get("this_week") is not None and params.get("this_week"):
            query_builder = query_builder.this_week()
        if params.get("this_month") is not None and params.get("this_month"):
            query_builder = query_builder.this_month()
        if params.get("after_date") is not None:
            query_builder = query_builder.after_date(params.get("after_date"))
        if params.get("before_date") is not None:
            query_builder = query_builder.before_date(params.get("before_date"))

        return query_builder


class GetThreadDetailsInput(BaseModel):
    """Input schema for getting thread details"""
    thread_id: str = Field(description="The ID of the thread to retrieve details for")


class GetThreadDetailsTool(BaseTool):
    """Tool for getting detailed information about a specific thread"""

    name: str = "get_thread_details"
    description: str = "Get detailed information about a specific email thread including all messages"
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
                        "body": msg.body,
                        "is_read": msg.is_read,
                        "is_starred": msg.is_starred,
                        "is_important": msg.is_important,
                        "labels": msg.labels,
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


class SummarizeThreadInput(BaseModel):
    """Input schema for summarizing a thread"""
    thread_id: str = Field(description="The ID of the thread to summarize")
    summary_type: Optional[str] = Field(
        default="conversation",
        description="Type of summary: 'conversation' (default), 'key_points', or 'action_items'"
    )


class SummarizeThreadTool(BaseTool):
    """Tool for summarizing email thread conversations"""

    name: str = "summarize_thread"
    description: str = "Summarize an email thread conversation, extracting key points or action items"
    args_schema: ArgsSchema = SummarizeThreadInput

    gmail_service: GmailApiService
    

    def __init__(self, gmail_service: GmailApiService, ):
        super().__init__(gmail_service=gmail_service)

    def _run(self, thread_id: str, summary_type: str = "conversation") -> dict:
        """Summarize a thread conversation"""
        try:
            
            thread = self.gmail_service.get_thread(thread_id)

            conversation_parts = []
            for msg in thread.messages:
                part = f"From: {msg.sender}\n"
                part += f"Date: {msg.date_time.isoformat() if msg.date_time else 'Unknown'}\n"
                part += f"Subject: {msg.subject}\n"
                part += f"Content: {msg.body}\n"
                conversation_parts.append(part)

            conversation_text = "\n---\n".join(conversation_parts)

            if summary_type == "key_points":
                summary_prompt = (
                    "Please identify the key points from this email thread conversation:\n"
                    "Only respond with the key points, NO ADDITIONAL TEXT"
                    f"{conversation_text}\n\n"
                    "Key Points:\n"
                )
            elif summary_type == "action_items":
                summary_prompt = (
                    "Please extract any action items, tasks, or follow-ups from this email thread:\n\n"
                    f"{conversation_text}\n\n"
                    "Action Items:\n"
                )
            else:  # conversation
                summary_prompt = (
                    "Please provide a concise summary of this email thread conversation:\n\n"
                    f"{conversation_text}\n\n"
                    "Summary:\n"
                )


            system_prompt = (
                "You are a helpful email thread summary assistant.\n"
                "You have the ability to concisely summarize threads, extract action items and identify key points.\n"
                "You should not perform any task other than these 3.\n"
                "When a user asks you to summarize, extract action items or identify key points, respond with that and NO ADDITIONAL TEXT."
            )

            llm = ChatGoogleGenerativeAI(MODELS['gemini']['flash'])
            summary = llm.invoke({
                "messages": [
                    SystemMessage(system_prompt),
                    HumanMessage(summary_prompt),
                ]})


            return {
                "status": "success",
                "thread_id": thread_id,
                "summary_type": summary_type,
                "summary": summary,
                "message": f"Thread summary generated successfully for thread_id {thread_id}"
            }

        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Error summarizing thread: {str(e)}"
            }


import asyncio
import json
import logging
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from typing import Optional, Union, Annotated

import filetype
from langchain_core.callbacks import adispatch_custom_event
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import ArgsSchema, InjectedToolArg
from pydantic import BaseModel, Field

from agents.common.tools import BaseGoogleTool
from core.auth import get_gmail_service, get_drive_service
from core.cache import get_email_cache
from core.supabase_client import upload_to_supabase
from google_client.services.gmail import EmailQueryBuilder
from google_client.services.gmail.async_query_builder import AsyncEmailQueryBuilder

logger = logging.getLogger(__name__)


class GetEmailInput(BaseModel):
    message_ids: list[str] = Field(description="The message_ids of the emails to retrieve")


class GetEmailTool(BaseGoogleTool):
    name: str = "get_emails"
    description: str = dedent("""
        - Fetches the full content of a single email and attachment metadata.
        - Requires a message_id.
    """)
    args_schema: ArgsSchema = GetEmailInput

    def _run(self, message_ids: list[str], config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, message_ids: list[str]) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Retrieving Email...", "icon": "📩"}
        )
        gmail = await get_gmail_service(config)
        email_cache = get_email_cache(config)

        email_map = {}
        missing_ids = []
        for message_id in message_ids:
            if cached := email_cache.get(message_id):
                email_map[message_id] = cached
            else:
                missing_ids.append(message_id)

        if missing_ids:
            fetched = await gmail.batch_get_emails(missing_ids)
            for result in fetched:
                if not isinstance(result, tuple):
                    email_map[result.message_id] = email_cache.save(result)

        emails = [email_map[mid] for mid in message_ids if mid in email_map]
        return json.dumps(emails)


class GetThreadDetailsInput(BaseModel):
    thread_ids: list[str] = Field(description="The IDs of the threads to retrieve details for")


class GetThreadDetailsTool(BaseGoogleTool):
    name: str = "get_thread_details"
    description: str = dedent("""
        - Fetches all messages in a thread in chronological order, including full content for each.
        - Requires a thread_id.
    """)
    args_schema: ArgsSchema = GetThreadDetailsInput

    def _run(self, thread_ids: list[str], config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, thread_ids: list[str]) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Retrieving Thread Details...", "icon": "🧵"}
        )
        gmail = await get_gmail_service(config)
        threads = await gmail.batch_get_threads(thread_ids)

        results = []
        for thread in threads:
            if isinstance(thread, tuple):
                logger.warning(f"Failed to fetch thread: {thread[1]}")
                continue
            results.append({
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
                        "body": msg.get_plain_text_content(),
                        "is_read": msg.is_read,
                        "is_starred": msg.is_starred,
                        "is_important": msg.is_important,
                        "organization": msg.labels,
                        "has_attachments": msg.has_attachments()
                    }
                    for msg in thread.messages
                ]
            })
        return json.dumps(results)


class SearchEmailsInput(BaseModel):
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
    with_labels: Optional[list[str]] = Field(default=None, description="Filter emails with specific labels")
    today: Optional[bool] = Field(default=None, description="Filter emails from today")
    yesterday: Optional[bool] = Field(default=None, description="Filter emails from yesterday")
    last_days: Optional[int] = Field(default=None, description="Filter emails from last N days")
    this_week: Optional[bool] = Field(default=None, description="Filter emails from this week")
    this_month: Optional[bool] = Field(default=None, description="Filter emails from this month")
    after_date: Optional[str] = Field(default=None, description="Filter emails after date (YYYY-MM-DD)")
    before_date: Optional[str] = Field(default=None, description="Filter emails before date (YYYY-MM-DD)")


def build_query(service, params: dict) -> Union[EmailQueryBuilder, AsyncEmailQueryBuilder]:
    query_builder = service.query()
    if params.get("include_promotions"):
        query_builder = query_builder.without_label(['promotions'])
    if params.get("limit"):
        query_builder = query_builder.limit(params.get("limit"))
    if params.get("search"):
        query_builder = query_builder.search(params.get("search"))
    if params.get("from_sender"):
        query_builder = query_builder.from_sender(params.get("from_sender"))
    if params.get("to_recipient"):
        query_builder = query_builder.to_recipient(params.get("to_recipient"))
    if params.get("with_subject"):
        query_builder = query_builder.with_subject(params.get("with_subject"))
    if params.get("with_attachments"):
        query_builder = query_builder.with_attachments()
    if params.get("is_read"):
        query_builder = query_builder.is_read()
    if params.get("is_unread"):
        query_builder = query_builder.is_unread()
    if params.get("is_starred"):
        query_builder = query_builder.is_starred()
    if params.get("is_important"):
        query_builder = query_builder.is_important()
    if params.get("in_folder"):
        query_builder = query_builder.in_folder(params.get("in_folder"))
    if params.get("with_labels"):
        query_builder = query_builder.with_label(params.get("with_labels"))
    if params.get("today"):
        query_builder = query_builder.today()
    if params.get("yesterday"):
        query_builder = query_builder.yesterday()
    if params.get("last_days"):
        query_builder = query_builder.last_days(params.get("last_days"))
    if params.get("this_week"):
        query_builder = query_builder.this_week()
    if params.get("this_month"):
        query_builder = query_builder.this_month()
    if params.get("after_date"):
        after_date = datetime.strptime(params.get("after_date"), "%Y-%m-%d")
        query_builder = query_builder.after_date(after_date)
    if params.get("before_date"):
        before_date = datetime.strptime(params.get("before_date"), "%Y-%m-%d")
        query_builder = query_builder.before_date(before_date)

    return query_builder


class SearchEmailsTool(BaseGoogleTool):
    name: str = "search_emails"
    description: str = dedent("""
        - Searches the user's mailbox and returns a list of matching email IDs, not email content.
        - Use this as the first step when the user refers to emails by description rather than a known ID.
        - Do NOT use this if you already have a message_id
        - Dates are non-inclusive (for emails on 2020-03-04, use after_date=2020-03-04, before_date=2020-03-05)
    """)
    args_schema: ArgsSchema = SearchEmailsInput

    def _run(
            self,
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
            with_labels: Optional[list[str]] = None,
            today: Optional[bool] = None,
            yesterday: Optional[bool] = None,
            last_days: Optional[int] = None,
            this_week: Optional[bool] = None,
            this_month: Optional[bool] = None,
            after_date: Optional[str] = None,
            before_date: Optional[str] = None,
            config: Annotated[RunnableConfig, InjectedToolArg] = None
    ) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(
            self,
            config: RunnableConfig,
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
            with_labels: Optional[list[str]] = None,
            today: Optional[bool] = None,
            yesterday: Optional[bool] = None,
            last_days: Optional[int] = None,
            this_week: Optional[bool] = None,
            this_month: Optional[bool] = None,
            after_date: Optional[str] = None,
            before_date: Optional[str] = None
    ) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Searching Emails...", "icon": "🔍"}
        )
        gmail = await get_gmail_service(config)
        email_cache = get_email_cache(config)
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
            "with_labels": with_labels,
            "today": today,
            "yesterday": yesterday,
            "last_days": last_days,
            "this_week": this_week,
            "this_month": this_month,
            "after_date": after_date,
            "before_date": before_date
        }

        query = build_query(gmail, params)
        message_ids = await query.execute()

        return "Here are the message_ids for the search query:\n" + json.dumps(message_ids)


class DownloadAttachmentInput(BaseModel):
    message_id: str = Field(description="Message ID of the writer containing the attachment")
    attachment_id: Optional[str] = Field(default=None,
                                         description="ID of the attachment to download. Leave empty to download all attachments in the email")


class DownloadAttachmentTool(BaseGoogleTool):
    name: str = "download_attachment"
    description: str = dedent("""
        - Downloads an attachment(s) from an email
        - Returns the paths of the attachments
        - To download a specific attachment(s) provide the attachment_id(s) as well. Otherwise, it will download all attachments in the email
        - Requires message_id
    """)
    args_schema: ArgsSchema = DownloadAttachmentInput

    def _run(self, message_id: str, attachment_id: Optional[str] = None,
             config: Annotated[RunnableConfig, InjectedToolArg] = None) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, message_id: str,
                               attachment_id: Optional[str] = None) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Downloading Attachment...", "icon": "📎"}
        )
        gmail = await get_gmail_service(config)
        email_cache = get_email_cache(config)
        user_id = config['configurable'].get('thread_id')

        email = email_cache.get(message_id)
        if email is None:
            email = email_cache.save(
                await gmail.get_email(message_id),
            )

        target_attachments = []
        if attachment_id is None:
            target_attachments = email["attachments"]
        else:
            for attachment in email["attachments"]:
                if attachment["attachment_id"] == attachment_id:
                    target_attachments = [attachment]
                    break

        if not target_attachments:
            return "No matching attachments found."

        async def process_attachment(attachment):
            attachment_data = {
                "message_id": message_id,
                "attachment_id": attachment["attachment_id"],
            }

            orig_file = Path(attachment["filename"])
            unique_filename = f"{orig_file.stem}_{uuid.uuid4().hex[:4]}{orig_file.suffix}"
            upload_path = f"{user_id}/{unique_filename}"

            attachment_bytes = await gmail.get_attachment_payload(attachment_data)
            mime_type = filetype.guess_mime(attachment_bytes) or "application/octet-stream"
            size = len(attachment_bytes)

            storage_path = await upload_to_supabase(
                path=upload_path,
                file_bytes=attachment_bytes,
                mime_type=mime_type
            )
            return {
                "filename": unique_filename,
                "path": storage_path,
                "mime_type": mime_type,
                "size": size,
            }

        # Process in parallel
        attachment_results = await asyncio.gather(
            *[process_attachment(a) for a in target_attachments],
            return_exceptions=True
        )

        # Filter out exceptions and log them
        results = []
        for res in attachment_results:
            if isinstance(res, Exception):
                logger.error(f"Failed to process attachment: {res}")
            else:
                results.append(res)

        return json.dumps(results)


class ListUserLabelsTool(BaseGoogleTool):
    name: str = "list_user_labels"
    description: str = dedent("""
        - Returns all user-created labels in the user's Gmail account along their label_ids. This doesn't include system labels like, INBOX, SENT, SPAM, etc.
        - Always call this first if label_id is unknown.
    """)

    def _run(self, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Listing Labels...", "icon": "🏷️"}
        )
        gmail = await get_gmail_service(config)
        labels = await gmail.list_labels()
        user_labels = [label for label in labels if label.type == "user"]
        user_labels = [{
            "label_id": label.id,
            "name": label.name
        } for label in user_labels
        ]
        return json.dumps(user_labels)

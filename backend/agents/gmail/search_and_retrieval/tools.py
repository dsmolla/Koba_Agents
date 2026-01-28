import json
import logging
import secrets
from datetime import datetime
from pathlib import Path
from typing import Optional, Union, Annotated

import filetype
from google.auth.exceptions import RefreshError
from google_client.services.gmail import EmailQueryBuilder
from google_client.services.gmail.async_query_builder import AsyncEmailQueryBuilder
from googleapiclient.errors import HttpError
from langchain_core.callbacks import adispatch_custom_event
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import ArgsSchema, InjectedToolArg
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from core.auth import get_gmail_service
from core.cache import get_email_cache
from core.exceptions import ProviderNotConnectedError
from core.supabase_client import upload_to_supabase

logger = logging.getLogger(__name__)


class GetEmailInput(BaseModel):
    message_id: str = Field(description="The message_id of the email to retrieve")


class GetEmailTool(BaseTool):
    name: str = "get_email"
    description: str = "Get email from Gmail by message_id"
    args_schema: ArgsSchema = GetEmailInput

    def _run(self, message_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(self, message_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        try:
            await adispatch_custom_event(
                "tool_status",
                {"text": "Retrieving Email...", "icon": "📩"}
            )
            gmail = await get_gmail_service(config)
            email_cache = get_email_cache(config)
            if (email := email_cache.get(message_id)) is None:
                email = email_cache.save(
                    await gmail.get_email(message_id=message_id)
                )

            return json.dumps(email)

        except (ProviderNotConnectedError, RefreshError):
            return "I currently don't have access to your gmail. Connect Gmail from the settings page."
        
        except HttpError as e:
            if e.status_code == 403:
                return "I currently don't have access to your gmail. Connect Gmail from the settings page."
            raise e

        except Exception as e:
            logger.error(f"Error in GetEmailTool: {e}", exc_info=True)
            return "Unable to fetch email due to internal error"


class GetThreadDetailsInput(BaseModel):
    thread_id: str = Field(description="The ID of the thread to retrieve details for")


class GetThreadDetailsTool(BaseTool):
    name: str = "get_thread_details"
    description: str = "Get detailed information about a specific writer thread including all messages"
    args_schema: ArgsSchema = GetThreadDetailsInput

    def _run(self, thread_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(self, thread_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        """Get detailed information about a specific thread"""
        try:
            await adispatch_custom_event(
                "tool_status",
                {"text": "Retrieving Thread Details...", "icon": "🧵"}
            )
            gmail = await get_gmail_service(config)
            thread = await gmail.get_thread(thread_id)

            result = {
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
            return json.dumps(result)

        except (ProviderNotConnectedError, RefreshError):
            return "I currently don't have access to your gmail. Connect Gmail from the settings page."
        
        except HttpError as e:
            if e.status_code == 403:
                return "I currently don't have access to your gmail. Connect Gmail from the settings page."
            raise e

        except Exception as e:
            logger.error(f"Error in GetThreadDetailsTool: {e}", exc_info=True)
            return "Unable to get thread details due to internal error"


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


class SearchEmailsTool(BaseTool):
    name: str = "search_emails"
    description: str = "search and retrieve emails from Gmail based on various filters. Returns email snippets"
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

    async def _arun(
            self,
            config: Annotated[RunnableConfig, InjectedToolArg],
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
        try:
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

            result = []
            not_in_cache = []

            for message_id in message_ids:
                if email := email_cache.get(message_id):
                    email = email.copy()
                    del email['body']
                    del email['attachments']
                    result.append(email)
                else:
                    not_in_cache.append(message_id)

            emails = await gmail.batch_get_emails(not_in_cache)
            for email in emails:
                if not isinstance(email, Exception):
                    temp = email_cache.save(email).copy()
                    del temp['body']
                    del temp['attachments']
                    result.append(temp)

            return json.dumps(result)

        except (ProviderNotConnectedError, RefreshError):
            return "I currently don't have access to your gmail. Connect Gmail from the settings page."
        
        except HttpError as e:
            if e.status_code == 403:
                return "I currently don't have access to your gmail. Connect Gmail from the settings page."
            raise e
        
        except Exception as e:
            logger.error(f"Error in SearchEmailsTool: {e}", exc_info=True)
            return "Unable to search emails due to internal error"


class DownloadAttachmentInput(BaseModel):
    message_id: str = Field(description="Message ID of the writer containing the attachment")
    attachment_id: Optional[str] = Field(default=None,
                                         description="ID of the attachment to download. Leave empty to download all attachments in the email")


class DownloadAttachmentTool(BaseTool):
    name: str = "download_attachment"
    description: str = "Download an attachment from an email message"
    args_schema: ArgsSchema = DownloadAttachmentInput

    def _run(self, message_id: str, attachment_id: Optional[str] = None,
             config: Annotated[RunnableConfig, InjectedToolArg] = None) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(self, message_id: str, config: Annotated[RunnableConfig, InjectedToolArg],
                    attachment_id: Optional[str] = None) -> str:
        try:
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

            attachments_downloaded = []
            if attachment_id is None:
                for attachment in email["attachments"]:
                    attachment_data = {
                        "message_id": message_id,
                        "attachment_id": attachment["attachment_id"],
                    }

                    short_id = secrets.token_hex(2)
                    file = Path(attachment["filename"])
                    filename = f"{file.stem}_{short_id}{file.suffix}"
                    upload_path = f"{user_id}/{filename}"
                    attachment_bytes = await gmail.get_attachment_payload(attachment_data)
                    mime_type = filetype.guess_mime(attachment_bytes)
                    size = len(attachment_bytes)

                    storage_path = await upload_to_supabase(
                        path=upload_path,
                        file_bytes=attachment_bytes,
                    )
                    attachments_downloaded.append(
                        {
                            "filename": filename,
                            "path": storage_path,
                            "mime_type": mime_type,
                            "size": size,
                        }
                    )

            else:
                file = None
                for attachment in email["attachments"]:
                    if attachment["attachment_id"] == attachment_id:
                        file = Path(attachment["filename"])
                        break

                attachment_data = {
                    "message_id": message_id,
                    "attachment_id": attachment_id,
                }
                short_id = secrets.token_hex(2)
                filename = f"{file.stem}_{short_id}{file.suffix}"
                upload_path = f"{user_id}/{filename}"
                attachment_bytes = await gmail.get_attachment_payload(attachment_data)
                mime_type = filetype.guess_mime(attachment_bytes)
                size = len(attachment_bytes)

                storage_path = await upload_to_supabase(
                    path=upload_path,
                    file_bytes=attachment_bytes,
                )
                attachments_downloaded.append(
                    {
                        "filename": filename,
                        "path": storage_path,
                        "mime_type": mime_type,
                        "size": size,
                    }
                )

            return json.dumps(attachments_downloaded)

        except (ProviderNotConnectedError, RefreshError):
            return "I currently don't have access to your gmail. Connect Gmail from the settings page."
        
        except HttpError as e:
            if e.status_code == 403:
                return "I currently don't have access to your gmail. Connect Gmail from the settings page."
            raise e

        except Exception as e:
            logger.error(f"Error in DownloadAttachmentTool: {e}", exc_info=True)
            return "Unable to download attachment due to internal error"


class ListUserLabelsTool(BaseTool):
    name: str = "list_user_labels"
    description: str = "List all user-created labels in Gmail. It does not include system organization like INBOX, SENT, SPAM, etc."

    def _run(self, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(self, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        try:
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
        except (ProviderNotConnectedError, RefreshError):
            return "I currently don't have access to your gmail. Connect Gmail from the settings page."
        
        except HttpError as e:
            if e.status_code == 403:
                return "I currently don't have access to your gmail. Connect Gmail from the settings page."
            raise e

        except Exception as e:
            logger.error(f"Error in ListUserLabelsTool: {e}", exc_info=True)
            return "Unable to list user labels due to internal error"

import asyncio
import logging
from textwrap import dedent
from typing import Annotated

from langchain_core.callbacks import adispatch_custom_event
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import ArgsSchema, InjectedToolArg
from pydantic import BaseModel, Field

from agents.common.tools import BaseGoogleTool
from core.auth import get_gmail_service

logger = logging.getLogger(__name__)


class ApplyLabelInput(BaseModel):
    message_ids: list[str] = Field(description="The Message IDs of the emails to label")
    label_id: str = Field(description=dedent(
        """
        The label_id to apply to the emails. Can be one of the following system labels:
            - SPAM
            - UNREAD
            - STARRED
            - IMPORTANT
            - CATEGORY_PERSONAL
            - CATEGORY_SOCIAL
            - CATEGORY_PROMOTIONS
            - CATEGORY_UPDATES
            - CATEGORY_FORUMS
        Or it can also be the label_id of any user created label.
        """
    ))


class ApplyLabelTool(BaseGoogleTool):
    name: str = "apply_label"
    description: str = "Apply a label to one or more emails in Gmail."
    args_schema: ArgsSchema = ApplyLabelInput

    def _run(self, message_ids: list[str], label_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, message_ids: list[str], label_id: str) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Applying Labels...", "icon": "📩"}
        )
        gmail = await get_gmail_service(config)
        results = await asyncio.gather(
            *[gmail.add_label(email=mid, labels=[label_id]) for mid in message_ids]
        )
        successes = sum(1 for r in results if r)
        return f"Label {label_id} applied to {successes} of {len(message_ids)} email(s)."


class RemoveLabelInput(BaseModel):
    message_ids: list[str] = Field(description="The Message IDs of the emails to remove the label from")
    label_id: str = Field(description=dedent(
        """
        The label_id to remove from the emails. Can be one of the following system labels:
            - SPAM
            - UNREAD
            - STARRED
            - IMPORTANT
            - CATEGORY_PERSONAL
            - CATEGORY_SOCIAL
            - CATEGORY_PROMOTIONS
            - CATEGORY_UPDATES
            - CATEGORY_FORUMS
        Or it can also be the label_id of any user created label.
        """
    ))


class RemoveLabelTool(BaseGoogleTool):
    name: str = "remove_label"
    description: str = "Remove a label from one or more emails."
    args_schema: ArgsSchema = RemoveLabelInput

    def _run(self, message_ids: list[str], label_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, message_ids: list[str], label_id: str) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Removing Label...", "icon": "🏷️"}
        )
        gmail = await get_gmail_service(config)
        results = await asyncio.gather(
            *[gmail.remove_label(email=mid, labels=[label_id]) for mid in message_ids]
        )
        successes = sum(1 for r in results if r)
        return f"Label {label_id} removed from {successes} of {len(message_ids)} email(s)."


class CreateLabelInput(BaseModel):
    name: str = Field(description="The name of the new label to create")


class CreateLabelTool(BaseGoogleTool):
    name: str = "create_label"
    description: str = "Create a new user label in Gmail"
    args_schema: ArgsSchema = CreateLabelInput

    def _run(self, name: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, name: str) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Creating Label...", "icon": "🏷️"}
        )
        gmail = await get_gmail_service(config)
        label = await gmail.create_label(name=name)
        return f"Created label {label.name} with label_id {label.id}"


class DeleteLabelInput(BaseModel):
    label_id: str = Field(description="The ID of the label to delete")


class DeleteLabelTool(BaseGoogleTool):
    name: str = "delete_label"
    description: str = "Delete a user-created label in Gmail"
    args_schema: ArgsSchema = DeleteLabelInput

    def _run(self, label_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, label_id: str) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Deleting Label...", "icon": "🗑️"}
        )
        gmail = await get_gmail_service(config)
        if await gmail.delete_label(label=label_id):
            return f"Label with label_id {label_id} deleted"

        return "Unable to delete label due to internal error"


class RenameLabelInput(BaseModel):
    label_id: str = Field(description="The ID of the label to rename")
    new_name: str = Field(description="The new name for the label")


class RenameLabelTool(BaseGoogleTool):
    name: str = "rename_label"
    description: str = "Rename a user-created label in Gmail"
    args_schema: ArgsSchema = RenameLabelInput

    def _run(self, label_id: str, new_name: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, label_id: str, new_name: str) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Renaming Label...", "icon": "🏷️"}
        )
        gmail = await get_gmail_service(config)
        label = await gmail.update_label(
            label=label_id,
            new_name=new_name,
        )
        return f"Label with label_id {label.id} renamed to {new_name}"


class DeleteEmailInput(BaseModel):
    message_ids: list[str] = Field(description="Message IDs of the emails to delete")


class DeleteEmailTool(BaseGoogleTool):
    name: str = "delete_emails"
    description: str = "Delete one or more email messages from Gmail. Emails are moved to Trash."
    args_schema: ArgsSchema = DeleteEmailInput

    def _run(self, message_ids: list[str], config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, message_ids: list[str]) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Deleting Email...", "icon": "🗑️"}
        )
        gmail = await get_gmail_service(config)
        results = await gmail.batch_delete_emails(emails=message_ids, permanent=False)
        successes = sum(1 for r in results if r is True)
        errors = sum(1 for r in results if isinstance(r, tuple))
        msg = f"{successes} of {len(message_ids)} email(s) deleted."
        if errors:
            msg += f" {errors} failed."
        return msg
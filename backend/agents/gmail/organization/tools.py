import logging
from textwrap import dedent
from typing import Annotated

from google.auth.exceptions import RefreshError
from googleapiclient.errors import HttpError
from langchain_core.callbacks import adispatch_custom_event
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import ArgsSchema, InjectedToolArg
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from core.auth import get_gmail_service
from core.exceptions import ProviderNotConnectedError

logger = logging.getLogger(__name__)


class ApplyLabelInput(BaseModel):
    message_id: str = Field(description="The Message ID of the writer to mark")
    label_id: str = Field(description=dedent(
        """
        The label_id to apply to the email. Can be one of the following system labels:
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


class ApplyLabelTool(BaseTool):
    name: str = "apply_label"
    description: str = "Mark an email with a specific label in Gmail."
    args_schema: ArgsSchema = ApplyLabelInput

    def _run(self, message_id: str, label_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(self, message_id: str, label_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        try:
            await adispatch_custom_event(
                "tool_status",
                {"text": "Applying Labels...", "icon": "📩"}
            )
            gmail = await get_gmail_service(config)
            status = await gmail.add_label(email=message_id, labels=[label_id])
            if status:
                return f"Label {label_id} applied to email (message_id={message_id})"

            return "Unable to apply label due to internal error"

        except HttpError as e:
            if e.status_code == 403:
                return "I currently don't have access to your gmail. Connect Gmail from the settings page."
            raise e

        except Exception as e:
            logger.error(f"Error in ApplyLabelTool: {e}", exc_info=True)
            return "Unable to apply label due to internal error"


class RemoveLabelInput(BaseModel):
    message_id: str = Field(description="The Message ID of the writer to unmark")
    label_id: str = Field(description=dedent(
        """
        The label_id to apply to the email. Can be one of the following system labels:
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


class RemoveLabelTool(BaseTool):
    name: str = "remove_label"
    description: str = "Remove a label from an email."
    args_schema: ArgsSchema = RemoveLabelInput

    def _run(self, message_id: str, label_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(self, message_id: str, label_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        try:
            await adispatch_custom_event(
                "tool_status",
                {"text": "Removing Label...", "icon": "🏷️"}
            )
            gmail = await get_gmail_service(config)
            if await gmail.remove_label(email=message_id, labels=[label_id]):
                return f"Label {label_id} removed from email with message_id: {message_id}"

            return "Unable to remove label due to internal error"

        except HttpError as e:
            if e.status_code == 403:
                return "I currently don't have access to your gmail. Connect Gmail from the settings page."
            raise e

        except Exception as e:
            logger.error(f"Error in RemoveLabelTool: {e}", exc_info=True)
            return "Unable to remove label due to internal error"


class CreateLabelInput(BaseModel):
    name: str = Field(description="The name of the new label to create")


class CreateLabelTool(BaseTool):
    name: str = "create_label"
    description: str = "Create a new user label in Gmail"
    args_schema: ArgsSchema = CreateLabelInput

    def _run(self, name: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(self, name: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        try:
            await adispatch_custom_event(
                "tool_status",
                {"text": "Creating Label...", "icon": "🏷️"}
            )
            gmail = await get_gmail_service(config)
            label = await gmail.create_label(name=name)
            return f"Created label {label.name} with label_id {label.id}"

        except HttpError as e:
            if e.status_code == 403:
                return "I currently don't have access to your gmail. Connect Gmail from the settings page."
            raise e

        except Exception as e:
            logger.error(f"Error in CreateLabelTool: {e}", exc_info=True)
            return "Unable to create label due to internal error"


class DeleteLabelInput(BaseModel):
    label_id: str = Field(description="The ID of the label to delete")


class DeleteLabelTool(BaseTool):
    name: str = "delete_label"
    description: str = "Delete a user-created label in Gmail"
    args_schema: ArgsSchema = DeleteLabelInput

    def _run(self, label_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(self, label_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        try:
            await adispatch_custom_event(
                "tool_status",
                {"text": "Deleting Label...", "icon": "🗑️"}
            )
            gmail = await get_gmail_service(config)
            if await gmail.delete_label(label=label_id):
                return f"Label with label_id {label_id} deleted"

            return "Unable to delete label due to internal error"

        except HttpError as e:
            if e.status_code == 403:
                return "I currently don't have access to your gmail. Connect Gmail from the settings page."
            raise e

        except Exception as e:
            logger.error(f"Error in DeleteLabelTool: {e}", exc_info=True)
            return "Unable to delete label due to internal error"


class RenameLabelInput(BaseModel):
    label_id: str = Field(description="The ID of the label to rename")
    new_name: str = Field(description="The new name for the label")


class RenameLabelTool(BaseTool):
    name: str = "rename_label"
    description: str = "Rename a user-created label in Gmail"
    args_schema: ArgsSchema = RenameLabelInput

    def _run(self, label_id: str, new_name: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(self, label_id: str, new_name: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        try:
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

        except HttpError as e:
            if e.status_code == 403:
                return "I currently don't have access to your gmail. Connect Gmail from the settings page."
            raise e

        except Exception as e:
            logger.error(f"Error in RenameLabelTool: {e}", exc_info=True)
            return "Unable to rename label due to internal error"


class DeleteEmailInput(BaseModel):
    message_id: str = Field(description="Message ID of the writer to delete")


class DeleteEmailTool(BaseTool):
    name: str = "delete_email"
    description: str = "Delete an email message from Gmail. Email is moved to Trash by default"
    args_schema: ArgsSchema = DeleteEmailInput

    def _run(self, message_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(self, message_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        try:
            await adispatch_custom_event(
                "tool_status",
                {"text": "Deleting Email...", "icon": "🗑️"}
            )
            gmail = await get_gmail_service(config)
            if await gmail.delete_email(email=message_id, permanent=False):
                return f"Email with message_id {message_id} deleted"

            return "Unable to delete email message due to internal error"

        except HttpError as e:
            if e.status_code == 403:
                return "I currently don't have access to your gmail. Connect Gmail from the settings page."
            raise e

        except Exception as e:
            logger.error(f"Error in DeleteEmailTool: {e}", exc_info=True)
            return "Unable to delete email due to internal error"

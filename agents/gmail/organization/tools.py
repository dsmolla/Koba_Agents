from textwrap import dedent

from google_client.services.gmail.api_service import GmailApiService
from langchain.tools.base import BaseTool
from langchain_core.tools import ArgsSchema
from pydantic import BaseModel, Field

from shared.exceptions import ToolException
from shared.response import ToolResponse


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

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(self, message_id: str, label_id: str) -> ToolResponse:
        try:
            if self.gmail_service.add_label(email=message_id, labels=[label_id]):
                return ToolResponse(
                    status="success",
                    message=f"Label ({label_id}) applied to email with message_id: {message_id}",
                )

            return ToolResponse(
                status="error",
                message="Unable to apply label due to internal error. Try again."
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Unable to apply label due to {e}",
            )


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

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(self, message_id: str, label_id: str) -> ToolResponse:
        try:
            if self.gmail_service.remove_label(email=message_id, labels=[label_id]):
                return ToolResponse(
                    status="success",
                    message=f"Label {label_id} removed from email with message_id: {message_id}",
                )

            return ToolResponse(
                status="error",
                message="Unable to remove label due to internal error. Try again."
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Unable to remove label due to {e}",
            )


class CreateLabelInput(BaseModel):
    name: str = Field(description="The name of the new label to create")


class CreateLabelTool(BaseTool):
    name: str = "create_label"
    description: str = "Create a new user label in Gmail"
    args_schema: ArgsSchema = CreateLabelInput

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(self, name: str) -> ToolResponse:
        try:

            label = self.gmail_service.create_label(name=name)
            return ToolResponse(
                status="success",
                message=f"Created label {label.name} with label_id {label.id}",
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Unable to create label {e}",
            )


class DeleteLabelInput(BaseModel):
    label_id: str = Field(description="The ID of the label to delete")


class DeleteLabelTool(BaseTool):
    name: str = "delete_label"
    description: str = "Delete a user-created label in Gmail"
    args_schema: ArgsSchema = DeleteLabelInput

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(self, label_id: str) -> ToolResponse:
        try:

            if self.gmail_service.delete_label(label=label_id):
                return ToolResponse(
                    status="success",
                    message=f"Label with label_id {label_id} deleted",
                )

            return ToolResponse(
                status="error",
                message="Unable to delete label due to internal error. Try again.",
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Unable to delete label: {e}"
            )


class RenameLabelInput(BaseModel):
    label_id: str = Field(description="The ID of the label to rename")
    new_name: str = Field(description="The new name for the label")


class RenameLabelTool(BaseTool):
    name: str = "rename_label"
    description: str = "Rename a user-created label in Gmail"
    args_schema: ArgsSchema = RenameLabelInput

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(self, label_id: str, new_name: str) -> ToolResponse:
        try:

            label = self.gmail_service.update_label(
                label=label_id,
                new_name=new_name,
            )
            return ToolResponse(
                status="success",
                message=f"Label with label_id {label.id} renamed to {new_name}",
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Unable to rename label: {e}",
            )


class DeleteEmailInput(BaseModel):
    message_id: str = Field(description="Message ID of the writer to delete")


class DeleteEmailTool(BaseTool):
    name: str = "delete_email"
    description: str = "Delete an email message from Gmail. Email is moved to Trash by default"
    args_schema: ArgsSchema = DeleteEmailInput

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService, ):
        super().__init__(gmail_service=gmail_service)

    def _run(self, message_id: str) -> ToolResponse:
        """Delete an email"""
        try:

            if self.gmail_service.delete_email(email=message_id, permanent=False):
                return ToolResponse(
                    status="success",
                    message=f"Email with message_id {message_id} deleted",
                )

            return ToolResponse(
                status="error",
                message=f"Unable to delete email message {message_id}. Try again",
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to delete email: {e}"
            )

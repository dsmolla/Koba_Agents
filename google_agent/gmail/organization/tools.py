from textwrap import dedent

from google_client.api_service import APIServiceLayer
from langchain_core.tools import ArgsSchema
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from google_agent.shared.exceptions import ToolException
from google_agent.shared.response import ToolResponse


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

    google_service: APIServiceLayer

    def __init__(self, google_service: APIServiceLayer):
        super().__init__(google_service=google_service)

    def _run(self, message_id: str, label_id: str) -> ToolResponse:
        try:
            if self.google_service.gmail.add_label(email=message_id, labels=[label_id]):
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

    async def _arun(self, message_id: str, label_id: str) -> ToolResponse:
        try:
            if await self.google_service.async_gmail.add_label(email=message_id, labels=[label_id]):
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

    google_service: APIServiceLayer

    def __init__(self, google_service: APIServiceLayer):
        super().__init__(google_service=google_service)

    def _run(self, message_id: str, label_id: str) -> ToolResponse:
        try:
            if self.google_service.gmail.remove_label(email=message_id, labels=[label_id]):
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

    async def _arun(self, message_id: str, label_id: str) -> ToolResponse:
        try:
            if await self.google_service.async_gmail.remove_label(email=message_id, labels=[label_id]):
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

    google_service: APIServiceLayer

    def __init__(self, google_service: APIServiceLayer):
        super().__init__(google_service=google_service)

    def _run(self, name: str) -> ToolResponse:
        try:

            label = self.google_service.gmail.create_label(name=name)
            return ToolResponse(
                status="success",
                message=f"Created label {label.name} with label_id {label.id}",
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Unable to create label {e}",
            )

    async def _arun(self, name: str) -> ToolResponse:
        try:
            label = await self.google_service.async_gmail.create_label(name=name)
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

    google_service: APIServiceLayer

    def __init__(self, google_service: APIServiceLayer):
        super().__init__(google_service=google_service)

    def _run(self, label_id: str) -> ToolResponse:
        try:

            if self.google_service.gmail.delete_label(label=label_id):
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

    async def _arun(self, label_id: str) -> ToolResponse:
        try:
            if await self.google_service.async_gmail.delete_label(label=label_id):
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

    google_service: APIServiceLayer

    def __init__(self, google_service: APIServiceLayer):
        super().__init__(google_service=google_service)

    def _run(self, label_id: str, new_name: str) -> ToolResponse:
        try:

            label = self.google_service.gmail.update_label(
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

    async def _arun(self, label_id: str, new_name: str) -> ToolResponse:
        try:
            label = await self.google_service.async_gmail.update_label(
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

    google_service: APIServiceLayer

    def __init__(self, google_service: APIServiceLayer):
        super().__init__(google_service=google_service)

    def _run(self, message_id: str) -> ToolResponse:
        """Delete an email"""
        try:

            if self.google_service.gmail.delete_email(email=message_id, permanent=False):
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

    async def _arun(self, message_id: str) -> ToolResponse:
        """Delete an email"""
        try:
            if await self.google_service.async_gmail.delete_email(email=message_id, permanent=False):
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

from textwrap import dedent
from typing import List
from langchain.tools.base import BaseTool
from google_client.services.gmail.api_service import GmailApiService
from langchain_core.tools import ArgsSchema
from pydantic import BaseModel, Field

SYSTEM_LABELS = {
    "SPAM": "SPAM",
    "UNREAD": "UNREAD",
    "STARRED": "STARRED",
    "IMPORTANT": "IMPORTANT",
    "PERSONAL": "CATEGORY_PERSONAL",
    "SOCIAL": "CATEGORY_SOCIAL",
    "PROMOTIONS": "CATEGORY_PROMOTIONS",
    "UPDATES": "CATEGORY_UPDATES",
    "FORUMS": "CATEGORY_FORUMS",
}


class ListUserLabelsInput(BaseModel):
    """Input schema for listing user-created labels"""
    pass


class ListUserLabelsTool(BaseTool):
    """Tool for listing user-created labels"""

    name: str  = "list_user_labels"
    description: str  = dedent("""
    List all user-created labels in Gmail.
    This tool retrieves and displays all labels that the user has created in their Gmail account.
    It does not include system labels like INBOX, SENT, SPAM, etc.
    """)
    args_schema: ArgsSchema = ListUserLabelsInput

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(self) -> dict:
        """List all user-created labels"""
        try:
            labels = self.gmail_service.list_labels()
            user_labels = [label for label in labels if label.type == "user"]
            return {
                "status": "success",
                "labels": [{"label_id": label.id, "name": label.name} for label in user_labels]
            }

        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Failed to list user labels.{str(e)}"
            }


class MarkEmailInput(BaseModel):
    """Input schema for marking an email with labels"""
    message_id: str = Field(description="The Message ID of the email to mark")
    labels: List[str] = Field(description=(
        "A list of labels to apply to the email. Can be one of the system labels "
        "[SPAM, UNREAD, STARRED, IMPORTANT, PERSONAL, SOCIAL, PROMOTIONS, UPDATES, FORUMS] "
        "or a custom user-created label ID"
    ))


class MarkEmailTool(BaseTool):
    """Tool for marking an email with a specific label"""

    name: str  = "mark_email"
    description: str  = "Mark an email with a specific label in Gmail."
    args_schema: ArgsSchema = MarkEmailInput

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(self, message_id: str, labels: List[str]) -> dict:
        """Mark an email with a specific label"""
        try:
            processed_labels = [SYSTEM_LABELS[label] if label in SYSTEM_LABELS else label for label in labels]

            self.gmail_service.add_label(
                email=message_id,
                labels=processed_labels,
            )

            return {
                "status": "success",
                "message": f"Email with Message ID: {message_id} marked with labels: {', '.join(processed_labels)}."
            }

        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Failed to mark email: {str(e)}"
            }


class UnmarkEmailInput(BaseModel):
    """Input schema for unmarking an email with labels"""
    message_id: str = Field(description="The Message ID of the email to unmark")
    labels: List[str] = Field(description=(
        "A list of labels to remove from the email. Can be one of the following system labels "
        "[SPAM, UNREAD, STARRED, IMPORTANT, PERSONAL, SOCIAL, PROMOTIONS, UPDATES, FORUMS] "
        "or a custom user-created label ID (required)"
    ))



class UnmarkEmailTool(BaseTool):
    """Tool for unmarking an email with a specific label"""

    name: str  = "unmark_email"
    description: str  = "Unmark an email with a specific label in Gmail."
    args_schema: ArgsSchema = UnmarkEmailInput

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(self, message_id: str, labels: List[str]) -> dict:
        """Unmark an email with a specific label"""
        try:
            processed_labels = [SYSTEM_LABELS[label] if label in SYSTEM_LABELS else label for label in labels]

            self.gmail_service.remove_label(
                email=message_id,
                labels=processed_labels,
            )
            return {
                "status": "success",
                "message": f"Email with Message ID: {message_id} unmarked from label: {''.join(processed_labels)}."
            }

        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Failed to unmark email: {str(e)}"
            }


class CreateLabelInput(BaseModel):
    """Input schema for creating a new user label"""
    name: str = Field(description="The name of the new label to create")


class CreateLabelTool(BaseTool):
    """Tool for creating a new user label"""

    name: str  = "create_label"
    description: str  = "Create a new user label in Gmail"
    args_schema: ArgsSchema = CreateLabelInput

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(self, name: str) -> dict:
        """Create a new user label"""
        try:
            label = self.gmail_service.create_label(name=name)
            return {
                "status": "success",
                "label_id": label.id,
                "name": label.name,
                "message": f"Label created successfully with ID: {label.id} and Name: {label.name}"
            }

        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Failed to create label: {str(e)}"
            }


class DeleteLabelInput(BaseModel):
    """Input schema for deleting a user-created label"""
    label_id: str = Field(description="The ID of the label to delete")


class DeleteLabelTool(BaseTool):
    """Tool for deleting a user-created label"""

    name: str  = "delete_label"
    description: str  = "Delete a user-created label in Gmail"
    args_schema: ArgsSchema = DeleteLabelInput

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(self, label_id: str) -> dict:
        """Delete a user-created label"""
        try:
            self.gmail_service.delete_label(label=label_id)

            return {
                "status": "success",
                "message": f"Label with ID: {label_id} deleted successfully"
            }

        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Failed to delete label: {str(e)}"
            }


class RenameLabelInput(BaseModel):
    """Input schema for renaming a user-created label"""
    label_id: str = Field(description="The ID of the label to rename")
    new_name: str = Field(description="The new name for the label")


class RenameLabelTool(BaseTool):
    """Tool for renaming a user-created label"""

    name: str  = "rename_label"
    description: str  = "Rename a user-created label in Gmail"
    args_schema: ArgsSchema = RenameLabelInput

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(self, label_id: str, new_name: str) -> dict:
        """Rename a user-created label"""
        try:
            label = self.gmail_service.update_label(
                label=label_id,
                new_name=new_name,
            )
            return {
                "status": "success",
                "message": f"Label with ID: {label.id} renamed successfully to Name: {label.name}"
            }

        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Failed to rename label: {str(e)}"
            }






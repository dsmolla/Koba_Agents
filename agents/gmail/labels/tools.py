from enum import Enum
from textwrap import dedent
from typing import Optional, Union
import json
from langchain.tools.base import BaseTool
from google_client.services.gmail.api_service import GmailApiService

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


class ListUserLabelsTool(BaseTool):
    """Tool for listing user-created labels"""

    name: str  = "list_user_labels"
    description: str  = dedent("""
    List all user-created labels in Gmail.
    This tool retrieves and displays all labels that the user has created in their Gmail account.
    It does not include system labels like INBOX, SENT, SPAM, etc.
    """)

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(self, tool_input: Optional[str] = None) -> dict:
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


class ApplyLabelsTool(BaseTool):
    """Tool for marking an email with a specific label"""

    name: str  = "mark_email"
    description: str  = dedent("""
    Mark an email with a specific label in Gmail.
    Provide the following details:
    - message_id: The Message ID of the email to mark (required)
    - labels: A list of labels to apply to the email. 
                Can be one of the system labels [SPAM, UNREAD, STARRED, IMPORTANT, PERSONAL, SOCIAL, PROMOTIONS, UPDATES, FORUMS]
                or a custom user-created label ID (required)
    """)

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(self, tool_input: Union[str, dict]) -> dict:
        """Mark an email with a specific label"""
        try:
            if isinstance(tool_input, str):
                try:
                    params = json.loads(tool_input)
                except json.JSONDecodeError:
                    return {
                        "status": "error",
                        "error_type": "JSONDecodeError",
                        "error_message": "Invalid input: Please provide a valid JSON.",
                        "message": "Invalid input: Please provide a valid JSON."
                    }
            else:
                params = tool_input

            labels = params.get("labels")
            labels = [SYSTEM_LABELS[label] if label in SYSTEM_LABELS else label for label in labels]

            self.gmail_service.add_label(
                email=params.get("message_id"),
                labels=labels,
            )

            return {
                "status": "success",
                "message": f"Email with Message ID: {params.get('message_id')} marked with labels: {', '.join(labels)}."
            }

        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Failed to mark email: {str(e)}"
            }


class RemoveLabelsTool(BaseTool):
    """Tool for unmarking an email with a specific label"""

    name: str  = "unmark_email"
    description: str  = dedent("""
    Unmark an email with a specific label in Gmail.
    Provide the following details:
    - message_id: The Message ID of the email to unmark (required)
    - labels: A list of labels to remove from the email. 
                Can be one of the following system labels [SPAM, UNREAD, STARRED, IMPORTANT, PERSONAL, SOCIAL, PROMOTIONS, UPDATES, FORUMS]
                or a custom user-created label ID (required)
    """)

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(self, tool_input: Union[str, dict]) -> dict:
        """Unmark an email with a specific label"""
        try:
            if isinstance(tool_input, str):
                try:
                    params = json.loads(tool_input)
                except json.JSONDecodeError:
                    return {
                        "status": "error",
                        "error_type": "JSONDecodeError",
                        "error_message": "Invalid input: Please provide a valid JSON.",
                        "message": "Invalid input: Please provide a valid JSON."
                    }
            else:
                params = tool_input

            labels = params.get("label")
            labels = [SYSTEM_LABELS[label] if label in SYSTEM_LABELS else label for label in labels]

            self.gmail_service.remove_label(
                email=params.get("message_id"),
                labels=labels,
            )
            return {
                "status": "success",
                "message": f"Email with Message ID: {params.get('message_id')} unmarked from label: {''.join(labels)}."
            }

        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Failed to unmark email: {str(e)}"
            }


class CreateLabelTool(BaseTool):
    """Tool for creating a new user label"""

    name: str  = "create_label"
    description: str  = dedent("""
    Create a new user label in Gmail.
    Provide the following details:
    - name: The name of the new label to create (required)
    """)

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(self, tool_input: Union[str, dict]) -> dict:
        """Create a new user label"""
        try:
            if isinstance(tool_input, str):
                try:
                    params = json.loads(tool_input)
                except json.JSONDecodeError:
                    return {
                        "status": "error",
                        "error_type": "JSONDecodeError",
                        "error_message": "Invalid input: Please provide a valid JSON.",
                        "message": "Invalid input: Please provide a valid JSON."
                    }
            else:
                params = tool_input

            label = self.gmail_service.create_label(
                name=params.get("name"),
            )
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


class DeleteLabelTool(BaseTool):
    """Tool for deleting a user-created label"""

    name: str  = "delete_label"
    description: str  = dedent("""
    Delete a user-created label in Gmail.
    Provide the following details:
    - label_id: The ID of the label to delete (required)
    Note: System labels like INBOX, SENT, SPAM, etc. cannot be deleted.
    """)

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(self, tool_input: Union[str, dict]) -> dict:
        """Delete a user-created label"""
        try:
            if isinstance(tool_input, str):
                try:
                    params = json.loads(tool_input)
                except json.JSONDecodeError:
                    return {
                        "status": "error",
                        "error_type": "JSONDecodeError",
                        "error_message": "Invalid input: Please provide a valid JSON.",
                        "message": "Invalid input: Please provide a valid JSON."
                    }
            else:
                params = tool_input

            self.gmail_service.delete_label(
                label=params.get("label_id"),
            )

            return {
                "status": "success",
                "message": f"Label with ID: {params.get('label_id')} deleted successfully"
            }

        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Failed to delete label: {str(e)}"
            }


class RenameLabelTool(BaseTool):
    """Tool for renaming a user-created label"""

    name: str  = "rename_label"
    description: str  = dedent("""
    Rename a user-created label in Gmail.
    Provide the following details:
    - label_id: The ID of the label to rename (required)
    - new_name: The new name for the label (required)
    Note: System labels like INBOX, SENT, SPAM, etc. cannot be renamed.
    """)

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(self, tool_input: Union[str, dict]) -> dict:
        """Rename a user-created label"""
        try:
            if isinstance(tool_input, str):
                try:
                    params = json.loads(tool_input)
                except json.JSONDecodeError:
                    return {
                        "status": "error",
                        "error_type": "JSONDecodeError",
                        "error_message": "Invalid input: Please provide a valid JSON.",
                        "message": "Invalid input: Please provide a valid JSON."
                    }
            else:
                params = tool_input

            label = self.gmail_service.update_label(
                label=params.get("label_id"),
                new_name=params.get("new_name"),
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






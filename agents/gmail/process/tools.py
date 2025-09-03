from langchain.tools.base import BaseTool
from google_client.services.gmail.api_service import GmailApiService
from langchain_core.tools import ArgsSchema
from pydantic import BaseModel, Field


class GetEmailInput(BaseModel):
    """Input schema for retrieving email body"""
    message_id: str = Field(description="The Message ID of the email to summarize")

class GetEmailTool(BaseTool):
    """Tool for summarizing an email"""
    name: str = "get_email_body"
    description: str = "Get the body text of an email given the message id"
    args_schema: ArgsSchema = GetEmailInput

    gmail_service: GmailApiService

    def __init__(self, gmail_service: GmailApiService):
        super().__init__(gmail_service=gmail_service)

    def _run(self, message_id: str) -> dict:
        try:
            message = self.gmail_service.get_email(message_id=message_id)
            return {
                "status": "success",
                "message": "Email body successfully retrieved",
                "body": message.get_plaintext(),
            }
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Failed to retrieve body of email"
            }





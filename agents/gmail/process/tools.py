from langchain.tools.base import BaseTool
from google_client.services.gmail.api_service import GmailApiService
from langchain_core.tools import ArgsSchema
from pydantic import BaseModel, Field
from typing import Literal


class SummarizeEmailInput(BaseModel):
    """Input schema for summarizing an email"""
    detail: Literal["brief", "detailed"] = Field(description="How to summarize the email can only be one of brief or detailed")

class SummarizeEmailTool(BaseTool):
    """Tool for summarizing an email"""
    name: str = "summarize_email"
    description: str = "Summarize an email"
    args_schema: ArgsSchema = SummarizeEmailInput

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





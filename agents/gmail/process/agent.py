from typing import Any

from langchain_core.language_models import BaseChatModel
from langgraph.prebuilt import create_react_agent
from google_client.services.gmail.api_service import GmailApiService
from langchain_anthropic import ChatAnthropic
from textwrap import dedent

from .tools import GetEmailTool



class ProcessAgent:
    def __init__(
            self,
            gmail_service: GmailApiService,
            llm: BaseChatModel = None
    ):
        self.llm = llm
        if self.llm is None:
            self.llm = ChatAnthropic(model_name='claude-3-5-sonnet-latest')

        self.tools = self._get_tools(gmail_service)
        self.system_prompt = self._get_system_prompt()


    @staticmethod
    def _get_tools(gmail_service: GmailApiService) -> list:
        return [GetEmailTool(gmail_service)]

    @staticmethod
    def _get_system_prompt():
        return dedent(
            """
            You are a email management assistant that can:
                - Classify emails
                - Summarize emails
            Use the provided tools to get the full content of the emails.
            Do not try to do anything other than the above 2 tasks.
            If the task is to classify email:
                1. Call the get_email_body tool
                2. Respond with:
                    {
                        "status": "success",
                        "message": "Successfully classified email",
                        "classification": [CLASSIFICATION]
                    }
                    
            
            If the task is to summarize email:
                1. Call the get_email_body tool
                2. Respond with:
                    {
                        "status": "success",
                        "message": "Successfully summarized email",
                        "summary": [SUMMARY]
                    }
            
            If there is any error, respond with:
                {
                    "status": "error",
                    "message": [ERROR_MESSAGE]
                }
            
            When finished, respond with FINISH.                        
            """
        )

    def create_agent(self):
        return create_react_agent(
            self.llm,
            tools=self.tools,
            prompt=self.system_prompt,
        )

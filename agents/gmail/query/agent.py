from typing import Any

from langchain_core.language_models import BaseChatModel
from langgraph.prebuilt import create_react_agent
from google_client.services.gmail.api_service import GmailApiService
from langchain_anthropic import ChatAnthropic
from textwrap import dedent

from .tools import (
    QueryEmailsTool,
    QueryThreadsTool
)


class QueryAgent:
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
        return [
            QueryEmailsTool(gmail_service),
            QueryThreadsTool(gmail_service)
        ]

    @staticmethod
    def _get_system_prompt():
        return dedent(
            """
            You are a helpful email query assistant that can:
                - Query Emails with various filters (sender, recipient, subject, date, labels, etc.)
                - Query Email Threads with various filters
            Use the provided tools to complete the task requested by the user.
            If unsure ask clarifying questions.
            Do not make up any data.
            When finished, respond with FINISH.                        
            """
        )

    def create_agent(self):
        return create_react_agent(
            self.llm,
            tools=self.tools,
            prompt=self.system_prompt,
        )


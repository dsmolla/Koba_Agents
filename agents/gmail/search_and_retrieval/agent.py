from datetime import datetime
from textwrap import dedent
from typing import Optional

from google_client.services.gmail.api_service import GmailApiService
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from agents.gmail.shared.email_cache import EmailCache
from .tools import GetEmailTool, SearchEmailsTool, ListUserLabelsTool, DownloadAttachmentTool
from ..shared.base_agent import BaseGmailAgent


class SearchAndRetrievalAgent(BaseGmailAgent):
    name = "RetrievalAgent"
    description = "Agent that can handle tasks related to organizing a gmail inbox"

    def __init__(
            self,
            gmail_service: GmailApiService,
            llm: BaseChatModel,
            email_cache: EmailCache,
            config: Optional[RunnableConfig] = None,
            print_steps: Optional[bool] = False,
    ):
        self.email_cache = email_cache
        super().__init__(gmail_service, llm, config, print_steps)

    def _get_tools(self):
        return [
            GetEmailTool(self.gmail_service, self.email_cache),
            SearchEmailsTool(self.gmail_service, self.email_cache),
            DownloadAttachmentTool(self.gmail_service, self.email_cache),
            ListUserLabelsTool(self.gmail_service)
        ]

    def system_prompt(self):
        tool_descriptions = []
        for tool in self.tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")

        return dedent(
            f"""
            # Identity

            You are a Gmail search and retrieval assistant that helps users search their inbox. You have access to the following Gmail tools:
            {'\n'.join(tool_descriptions)}

            # Instructions

            * Think step-by-step: Break down requests into smaller requests for each tool.
            * Plan your approach: Identify the tools you need and in what order.
            * Check tool responses: Always verify results before returning to user.
            * Final response: At the end, respond with results of the tool_calls.
            * Always include message_ids in your response.
            * Always include FULL FILE PATHS in your response when downloading attachments.

            CURRENT DATE AND TIME: {datetime.now().strftime("%Y-%m-%d %H:%M")}

        """)


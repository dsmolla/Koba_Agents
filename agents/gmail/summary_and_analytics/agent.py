from textwrap import dedent
from typing import Dict, List, Optional

from google_client.services.gmail.api_service import GmailApiService
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from agents.gmail.shared.email_cache import EmailCache
from .tools import SummarizeEmailsTool, ExtractFromEmailTool, ClassifyEmailTool
from ..shared.base_agent import BaseGmailAgent


class SummaryAndAnalyticsAgent(BaseGmailAgent):
    name = "SummaryAndAnalyticsAgent"
    description = "Agent that helps users search their inbox"

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
            SummarizeEmailsTool(self.gmail_service, self.email_cache),
            ExtractFromEmailTool(self.gmail_service, self.email_cache),
            ClassifyEmailTool(self.gmail_service, self.email_cache),
        ]

    def system_prompt(self) -> str:
        tool_descriptions = []
        for tool in self.tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")

        return dedent(
            f"""
            # Identity

            You are a Gmail summary and analytics assistant that helps users summarize their emails. You have access to the following Gmail tools:
            {'\n'.join(tool_descriptions)}

            # Instructions

            * Think step-by-step: Break down requests into smaller requests for each tool.
            * Plan your approach: Identify the tools you need and in what order.
            * Check tool responses: Always verify results before returning to user.
            * Final response: At the end, respond with results of the tool_calls. Make sure to always include message_ids in your response

        """)


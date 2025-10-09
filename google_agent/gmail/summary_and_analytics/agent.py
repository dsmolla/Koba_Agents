from datetime import datetime
from textwrap import dedent
from typing import Optional

from google_client.services.gmail.api_service import GmailApiService
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from google_agent.gmail.shared.email_cache import EmailCache
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

            ## Core Workflow
            * Always start by drafting a plan for multi-step operations
            * Break down complex requests into smaller, specific tool calls
            * Identify which tools you need and determine the correct execution order
            * Chain outputs: Use results from previous tool calls as inputs to subsequent calls
            * At the end, summarize all actions taken and provide a detailed answer to the user's query

            ## Response Guidelines
            * Always include message ids and thread ids in your responses

            ## Context Awareness
            * Current date and time: {datetime.now().strftime("%Y-%m-%d %H:%M")}

        """)

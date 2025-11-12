from textwrap import dedent
from typing import Optional

from google_client.api_service import APIServiceLayer
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from google_agent.gmail.shared.email_cache import EmailCache
from .tools import SummarizeEmailsTool, ExtractFromEmailTool, ClassifyEmailTool
from ..shared.base_agent import BaseGmailAgent
from ...shared.tools import CurrentDateTimeTool


class SummaryAndAnalyticsAgent(BaseGmailAgent):
    name = "SummaryAndAnalyticsAgent"
    description = "Agent that helps users search their inbox"

    def __init__(
            self,
            google_service: APIServiceLayer,
            llm: BaseChatModel,
            email_cache: EmailCache,
            config: Optional[RunnableConfig] = None
    ):
        self.email_cache = email_cache
        super().__init__(google_service, llm, config)

    def _get_tools(self):
        return [
            CurrentDateTimeTool(self.google_service.timezone),
            SummarizeEmailsTool(self.google_service, self.email_cache),
            ExtractFromEmailTool(self.google_service, self.email_cache),
            ClassifyEmailTool(self.google_service, self.email_cache),
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
            * Use the current_datetime_tool to get the current date and time when needed
            
        """)

from datetime import datetime
from textwrap import dedent
from typing import Optional

from google_client.api_service import APIServiceLayer
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from google_agent.gmail.shared.email_cache import EmailCache
from .tools import GetEmailTool, SearchEmailsTool, ListUserLabelsTool, DownloadAttachmentTool
from ..shared.base_agent import BaseGmailAgent
from ...shared.tools import CurrentDateTimeTool


class SearchAndRetrievalAgent(BaseGmailAgent):
    name = "RetrievalAgent"
    description = "Agent that can handle tasks related to organizing a gmail inbox"

    def __init__(
            self,
            google_service: APIServiceLayer,
            llm: BaseChatModel,
            email_cache: EmailCache,
            config: Optional[RunnableConfig] = None,
            print_steps: Optional[bool] = False,
    ):
        self.email_cache = email_cache
        super().__init__(google_service, llm, config, print_steps)

    def _get_tools(self):
        return [
            CurrentDateTimeTool(self.google_service.timezone),
            GetEmailTool(self.google_service, self.email_cache),
            SearchEmailsTool(self.google_service, self.email_cache),
            DownloadAttachmentTool(self.google_service, self.email_cache),
            ListUserLabelsTool(self.google_service)
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

            ## Core Workflow
            * Always start by drafting a plan for multi-step operations
            * Break down complex requests into smaller, specific tool calls
            * Identify which tools you need and determine the correct execution order
            * Chain outputs: Use results from previous tool calls as inputs to subsequent calls
            * At the end, summarize all actions taken and provide a detailed answer to the user's query

            ## Response Guidelines
            * Always include message ids and thread ids in your responses
            * Always include Label IDs in your response when listing or modifying labels
            * Always include FULL FILE PATHS in your response for downloaded attachments
            * Always provide clear, organized results

            ## Context Awareness
            * Use the current_datetime_tool to get the current date and time when needed
            
        """)


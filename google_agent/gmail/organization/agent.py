from datetime import datetime
from textwrap import dedent
from typing import Optional

from google_client.services.gmail.api_service import GmailApiService
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from .tools import ApplyLabelTool, RemoveLabelTool, CreateLabelTool, DeleteLabelTool, RenameLabelTool, DeleteEmailTool
from ..shared.base_agent import BaseGmailAgent


class OrganizationAgent(BaseGmailAgent):
    name = "OrganizationAgent"
    description = "Agent that can handle tasks related to organizing a gmail inbox"

    def __init__(
            self,
            gmail_service: GmailApiService,
            llm: BaseChatModel,
            config: Optional[RunnableConfig] = None,
            print_steps: Optional[bool] = False,
    ):
        super().__init__(gmail_service, llm, config, print_steps)

    def _get_tools(self):
        return [
            ApplyLabelTool(self.gmail_service),
            RemoveLabelTool(self.gmail_service),
            CreateLabelTool(self.gmail_service),
            DeleteLabelTool(self.gmail_service),
            RenameLabelTool(self.gmail_service),
            DeleteEmailTool(self.gmail_service)
        ]

    def system_prompt(self):
        tool_descriptions = []
        for tool in self.tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")

        return dedent(
            f"""
            # Identity

            You are a Gmail organization assistant that helps users manage their email organization. You have access to the following Gmail tools:
            {'\n'.join(tool_descriptions)}

            # Instructions

            * Think step-by-step: Break down requests into smaller requests for each tool.
            * Plan your approach: Identify the tools you need and in what order.
            * Check tool responses: Always verify results before returning to user.
            * Final response: At the end, respond with results of the tool_calls.

            CURRENT DATE AND TIME: {datetime.now().strftime("%Y-%m-%d %H:%M")}

        """)

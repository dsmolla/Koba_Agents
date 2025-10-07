from datetime import datetime
from textwrap import dedent
from typing import Optional

from google_client.services.gmail.api_service import GmailApiService
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from .tools import SendEmailTool, DraftEmailTool, ReplyEmailTool, ForwardEmailTool
from ..shared.base_agent import BaseGmailAgent


class WriterAgent(BaseGmailAgent):
    name = "WriterAgent"
    description = "Agent that can deals with sending, drafting, forwarding and replying of emails"

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
            SendEmailTool(self.gmail_service),
            DraftEmailTool(self.gmail_service),
            ReplyEmailTool(self.gmail_service),
            ForwardEmailTool(self.gmail_service)
        ]

    def system_prompt(self):
        tool_descriptions = []
        for tool in self.tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")

        return dedent(
            f"""
            # Identity

            You are a Gmail assistant that helps users with write operations. You have access to the following Gmail tools:
            {'\n'.join(tool_descriptions)}

            # Instructions

            * Think step-by-step: Break down requests into smaller requests for each tool.
            * Plan your approach: Identify the tools you need and in what order.
            * Check tool responses: Always verify results before returning to user.
            * Final response: At the end, respond with results of the tool_calls.

            CURRENT DATE AND TIME: {datetime.now().strftime("%Y-%m-%d %H:%M")}
        """)


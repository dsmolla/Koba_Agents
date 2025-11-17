from textwrap import dedent

from google_client.api_service import APIServiceLayer
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from .tools import SendEmailTool, DraftEmailTool, ReplyEmailTool, ForwardEmailTool
from ...shared.base_agent import BaseReActAgent


class WriterAgent(BaseReActAgent):
    name = "GmailWriterAgent"
    description = "Agent that can deals with sending, drafting, forwarding and replying of emails"

    def __init__(
            self,
            google_service: APIServiceLayer,
            llm: BaseChatModel,
            config: RunnableConfig = None,
    ):
        super().__init__(llm, google_service, config)

    def tools(self):
        return [
            SendEmailTool(self.google_service),
            DraftEmailTool(self.google_service),
            ReplyEmailTool(self.google_service),
            ForwardEmailTool(self.google_service)
        ]

    def system_prompt(self):
        tool_descriptions = []
        for tool in self.tools():
            tool_descriptions.append(f"- {tool.name}: {tool.description}")

        return dedent(
            f"""
            # Identity

            You are a Gmail assistant that helps users with write operations. You have access to the following Gmail tools:
            {'\n'.join(tool_descriptions)}

            # Instructions

            *## Core Workflow
            * Always start by drafting a plan for multi-step operations
            * Break down complex requests into smaller, specific tool calls
            * Identify which tools you need and determine the correct execution order
            * Chain outputs: Use results from previous tool calls as inputs to subsequent calls
            * At the end, summarize all actions taken and provide a detailed answer to the user's query

            ## Response Guidelines
            * Always include message ids and thread ids in your responses
        """)

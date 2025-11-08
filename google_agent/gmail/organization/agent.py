from datetime import datetime
from textwrap import dedent
from typing import Optional

from google_client.api_service import APIServiceLayer
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from .tools import ApplyLabelTool, RemoveLabelTool, CreateLabelTool, DeleteLabelTool, RenameLabelTool, DeleteEmailTool
from ..shared.base_agent import BaseGmailAgent


class OrganizationAgent(BaseGmailAgent):
    name = "OrganizationAgent"
    description = "Agent that can handle tasks related to organizing a gmail inbox"

    def __init__(
            self,
            google_service: APIServiceLayer,
            llm: BaseChatModel,
            config: Optional[RunnableConfig] = None,
            print_steps: Optional[bool] = False,
    ):
        super().__init__(google_service, llm, config, print_steps)

    def _get_tools(self):
        return [
            ApplyLabelTool(self.google_service),
            RemoveLabelTool(self.google_service),
            CreateLabelTool(self.google_service),
            DeleteLabelTool(self.google_service),
            RenameLabelTool(self.google_service),
            DeleteEmailTool(self.google_service)
        ]

    def system_prompt(self):
        tool_descriptions = []
        for tool in self.tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")

        return dedent(
            f"""
            # Identity

            You are a Gmail organization assistant that helps users with their email organization. You have access to the following Gmail tools:
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
            * Always provide clear, organized results

            ## Context Awareness
            * Current date and time: {datetime.now().strftime("%Y-%m-%d %H:%M")}
        """)

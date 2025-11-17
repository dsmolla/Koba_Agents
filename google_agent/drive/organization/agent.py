from textwrap import dedent

from .tools import MoveFileTool, RenameFileTool, DeleteFileTool

from google_client.api_service import APIServiceLayer
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from ...shared.base_agent import BaseReActAgent


class OrganizationAgent(BaseReActAgent):
    name: str = "DriveOrganizationAgent"
    description: str = "Specialized drive agent for moving, renaming, and deleting Google Drive files and folders"

    def __init__(
            self,
            google_service: APIServiceLayer,
            llm: BaseChatModel,
            config: RunnableConfig = None,
    ):
        super().__init__(llm, google_service, config)

    def tools(self):
        return [
            MoveFileTool(self.google_service),
            RenameFileTool(self.google_service),
            DeleteFileTool(self.google_service),
        ]

    def system_prompt(self):
        tool_descriptions = []
        for tool in self.tools():
            tool_descriptions.append(f"- {tool.name}: {tool.description}")

        return dedent(
            f"""
            # Identity

            You are a Google Drive organization specialist. You excel at organizing, managing, and maintaining Drive files and folders. You have access to the following tools:
            {'\n'.join(tool_descriptions)}

            # Instructions
            
            ## Core Workflow
            * Always start by drafting a plan for multi-step operations
            * Break down complex requests into smaller, specific tool calls
            * Identify which tools you need and determine the correct execution order
            * Chain outputs: Use results from previous tool calls as inputs to subsequent calls
            * At the end, summarize all actions taken and provide a detailed answer to the user's query

            ## Response Guidelines
            * Always include file IDs in your responses
            * Always provide clear, organized results
            """
        )

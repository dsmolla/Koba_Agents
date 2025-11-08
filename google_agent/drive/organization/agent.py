from datetime import datetime
from textwrap import dedent

from google_agent.drive.shared.base_agent import BaseDriveAgent
from .tools import MoveFileTool, RenameFileTool, DeleteFileTool


class OrganizationAgent(BaseDriveAgent):
    name: str = "OrganizationAgent"
    description: str = "Specialized agent for organizing, managing, and maintaining Google Drive files and folders"

    def _get_tools(self):
        return [
            MoveFileTool(self.google_service),
            RenameFileTool(self.google_service),
            DeleteFileTool(self.google_service),
        ]

    def system_prompt(self):
        tool_descriptions = []
        for tool in self.tools:
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

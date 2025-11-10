from datetime import datetime
from textwrap import dedent

from google_agent.drive.shared.base_agent import BaseDriveAgent
from .tools import SearchFilesTool, GetFileTool, DownloadFileTool, ListFolderContentsTool, GetPermissionsTool
from ...shared.tools import CurrentDateTimeTool


class SearchAndRetrievalAgent(BaseDriveAgent):
    name: str = "SearchAndRetrievalAgent"
    description: str = "Specialized agent for searching, retrieving, and accessing Google Drive files and folders"

    def _get_tools(self):
        return [
            CurrentDateTimeTool(self.google_service.timezone),
            SearchFilesTool(self.google_service),
            GetFileTool(self.google_service),
            DownloadFileTool(self.google_service),
            ListFolderContentsTool(self.google_service),
            GetPermissionsTool(self.google_service),
        ]

    def system_prompt(self):
        tool_descriptions = []
        for tool in self.tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")

        return dedent(
            f"""
            # Identity

            You are a Google Drive search and retrieval specialist. You excel at finding, accessing, and retrieving information about files and folders. You have access to the following tools:
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
            * Always include FULL FILE PATHS in your response for downloaded files
            * Always provide clear, organized results

            ## Context Awareness
            * Use the current_datetime_tool to get the current date and time when needed
            
            """
        )

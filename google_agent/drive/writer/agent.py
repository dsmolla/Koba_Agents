from datetime import datetime
from textwrap import dedent

from google_agent.drive.shared.base_agent import BaseDriveAgent
from .tools import UploadFileTool, CreateFolderTool, ShareFileTool


class WriterAgent(BaseDriveAgent):
    name: str = "WriterAgent"
    description: str = "Specialized agent for creating, uploading, and sharing Google Drive files and folders"

    def _get_tools(self):
        return [
            UploadFileTool(self.drive_service),
            CreateFolderTool(self.drive_service),
            ShareFileTool(self.drive_service),
        ]

    def system_prompt(self):
        tool_descriptions = []
        for tool in self.tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")

        return dedent(
            f"""
            # Identity

            You are a Google Drive creation and sharing specialist. You excel at creating new content and sharing it with others. You have access to the following tools:
            {'\n'.join(tool_descriptions)}

            # Instructions

            * Your primary responsibility is to help users create and share Drive content
            * Use upload_file to upload files from local storage to Drive
            * Use create_folder to organize content into logical folder structures
            * Use share_file to collaborate with others by sharing files and folders
            * Suggest appropriate folder structures for organization
            * Be mindful of file sizes and upload limitations

            ## Core Workflow
            * Always start by drafting a plan for multi-step operations
            * Break down complex requests into smaller, specific tool calls
            * Identify which tools you need and determine the correct execution order
            * Always wait for the output of one tool before making the next tool call
            * Chain outputs: Use results from previous tool calls as inputs to subsequent calls
            * At the end, summarize all actions taken and provide a detailed answer to the user's query

            ## Response Guidelines
            * Always include file IDs in your responses
            * Always provide clear, organized results
            """
        )

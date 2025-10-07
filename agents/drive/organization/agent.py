from datetime import datetime
from textwrap import dedent
from typing import List

from google_client.services.drive import DriveApiService
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from agents.drive.shared.base_agent import BaseDriveAgent
from .tools import MoveFileTool, RenameFileTool, DeleteFileTool


class OrganizationAgent(BaseDriveAgent):
    name: str = "OrganizationAgent"
    description: str = "Specialized agent for organizing, managing, and maintaining Google Drive files and folders"

    def _get_tools(self):
        return [
            MoveFileTool(self.drive_service),
            RenameFileTool(self.drive_service),
            DeleteFileTool(self.drive_service),
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

            * Your primary responsibility is to help users organize their Drive files
            * Use move_file to relocate files and folders to better locations
            * Use rename_file to give files and folders more descriptive names
            * Use delete_file to remove unwanted files and folders
            * Always confirm destructive actions before proceeding
            * Suggest organizational improvements when appropriate
            * Be careful with delete operations as they are permanent

            CURRENT DATE AND TIME: {datetime.now().strftime("%Y-%m-%d %H:%M")}
            """
        )


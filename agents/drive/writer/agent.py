from datetime import datetime
from textwrap import dedent
from typing import List

from google_client.services.drive import DriveApiService
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from agents.drive.shared.base_agent import BaseDriveAgent
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
            * Always confirm sharing permissions before making files public
            * Suggest appropriate folder structures for organization
            * Be mindful of file sizes and upload limitations

            CURRENT DATE AND TIME: {datetime.now().strftime("%Y-%m-%d %H:%M")}
            """
        )
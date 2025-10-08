from datetime import datetime
from textwrap import dedent

from google_agent.drive.shared.base_agent import BaseDriveAgent
from .tools import SearchFilesTool, GetFileTool, DownloadFileTool, ListFolderContentsTool, GetPermissionsTool


class SearchAndRetrievalAgent(BaseDriveAgent):
    name: str = "SearchAndRetrievalAgent"
    description: str = "Specialized agent for searching, retrieving, and accessing Google Drive files and folders"

    def _get_tools(self):
        return [
            SearchFilesTool(self.drive_service),
            GetFileTool(self.drive_service),
            DownloadFileTool(self.drive_service),
            ListFolderContentsTool(self.drive_service),
            GetPermissionsTool(self.drive_service),
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

            * Your primary responsibility is to help users find and access their Drive files
            * Use search_files to locate files based on various criteria like name, type, date, etc.
            * Use get_file to get detailed information about specific files
            * Use download_file when users need file content
            * Use list_folder_contents to explore folder structures
            * Use get_permissions to check sharing settings
            * Always provide clear, organized results
            * Always include relevant file IDs since they are needed for follow-up actions
            * Always include file paths for downloaded files

            CURRENT DATE AND TIME: {datetime.now().strftime("%Y-%m-%d %H:%M")}
            """
        )

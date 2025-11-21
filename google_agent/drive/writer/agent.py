from textwrap import dedent

from google_agent.shared.base_agent import BaseReactGoogleAgent
from .tools import UploadFileTool, CreateFolderTool, ShareFileTool


class WriterAgent(BaseReactGoogleAgent):
    name: str = "WriterAgent"
    description: str = dedent("""
        Specialized agent for managing Google Drive files and folders with the following capabilities:
            - Upload files to Google Drive (needs file path and folder_id)
            - Create folders in Google Drive (needs folder name and optional parent folder_id)
            - Share files and folders with other users (needs file_id/folder_id)
    """)

    @property
    def tools(self):
        if self._tools is None:
            self._tools = [
                UploadFileTool(self.google_service),
                CreateFolderTool(self.google_service),
                ShareFileTool(self.google_service),
            ]
        return self._tools

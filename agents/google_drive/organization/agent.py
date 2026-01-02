from textwrap import dedent

from agents.shared.base_agent import BaseReactGoogleAgent
from .tools import MoveFileTool, RenameFileTool, DeleteFileTool


class OrganizationAgent(BaseReactGoogleAgent):
    name: str = "OrganizationAgent"
    description: str = dedent("""
        Specialized agent for organizing Google Drive files and folders with the following capabilities:
            - Move files and folders (needs file_id/folder_id and folder_id)
            - Rename files and folders (needs file_id or folder_id)
            - Delete files and folders (needs file_id or folder_id)
    """)

    @property
    def tools(self):
        if self._tools is None:
            self._tools = [
                MoveFileTool(self.google_service),
                RenameFileTool(self.google_service),
                DeleteFileTool(self.google_service),
            ]
        return self._tools

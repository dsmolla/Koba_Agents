from textwrap import dedent

from google_agent.shared.base_agent import BaseReactGoogleAgent
from .tools import SearchFilesTool, GetFileTool, DownloadFileTool, ListFolderContentsTool, GetPermissionsTool
from ...shared.tools import CurrentDateTimeTool


class SearchAndRetrievalAgent(BaseReactGoogleAgent):
    name: str = "SearchAndRetrievalAgent"
    description: str = dedent("""
        Specialized agent for searching and retrieving Google Drive files and folders with the following capabilities:
            - Search for files and folders based on various criteria
            - Retrieve file/folder metadata and content (needs file_id or folder_id)
            - Download files (needs file_id)
            - List contents of folders (needs folder_id)
            - Get sharing permissions of files and folders (needs file_id or folder_id)
    """)

    def __init__(self, google_service, llm, config=None, download_folder=None):
        super().__init__(google_service, llm, config)
        self.download_folder = download_folder

    @property
    def tools(self):
        if self._tools is None:
            self._tools = [
                CurrentDateTimeTool(self.google_service.timezone),
                SearchFilesTool(self.google_service),
                GetFileTool(self.google_service),
                DownloadFileTool(self.google_service, self.download_folder),
                ListFolderContentsTool(self.google_service),
                GetPermissionsTool(self.google_service),
            ]
        return self._tools

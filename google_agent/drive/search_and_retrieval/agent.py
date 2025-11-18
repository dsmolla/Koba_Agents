from textwrap import dedent

from google_client.api_service import APIServiceLayer
from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from .system_prompt import system_prompt
from .tools import SearchFilesTool, GetFileTool, DownloadFileTool, ListFolderContentsTool, GetPermissionsTool


class SearchAndRetrievalAgent:
    name: str = "DriveSearchAndRetrievalAgent"
    description: str = dedent("""
        This agent can:
            - Search for files and folders in Google Drive based on various criteria
            - Retrieve metadata and content of specific files from Google Drive
            - Download files from Google Drive
            - List contents of folders in Google Drive
            - Get permissions and sharing settings of files and folders in Google Drive
        """)

    def __init__(
            self,
            google_service: APIServiceLayer,
            llm: BaseChatModel,
            config: RunnableConfig = None,
    ):
        self._tools = [
            SearchFilesTool(google_service),
            GetFileTool(google_service),
            DownloadFileTool(google_service),
            ListFolderContentsTool(google_service),
            GetPermissionsTool(google_service),
        ]

        self.agent = create_agent(
            name=self.name,
            model=llm,
            tools=self._tools,
            system_prompt=system_prompt.format(
                tools="\n".join([f"- {tool.name}: {tool.description}" for tool in self._tools])),
        )

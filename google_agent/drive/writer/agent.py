from textwrap import dedent

from google_client.api_service import APIServiceLayer
from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from .system_prompt import system_prompt
from .tools import UploadFileTool, CreateFolderTool, ShareFileTool


class WriterAgent:
    name: str = "DriveWriterAgent"
    description: str = dedent("""
        This agent can:
            - Upload files to Google Drive
            - Create new folders in Google Drive
            - Share files and folders with other users in Google Drive  
    """)
    def __init__(
            self,
            google_service: APIServiceLayer,
            llm: BaseChatModel,
            config: RunnableConfig = None,
    ):
        self._tools = [
            UploadFileTool(google_service),
            CreateFolderTool(google_service),
            ShareFileTool(google_service),
        ]

        self.agent = create_agent(
            name=self.name,
            model=llm,
            tools=self._tools,
            system_prompt=system_prompt.format(
                tools="\n".join([f"- {tool.name}: {tool.description}" for tool in self._tools])),
        )

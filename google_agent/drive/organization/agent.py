from google_client.api_service import APIServiceLayer
from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from .system_prompt import system_prompt
from .tools import MoveFileTool, RenameFileTool, DeleteFileTool


class OrganizationAgent:
    name: str = "DriveOrganizationAgent"
    description: str = """
    This agent can:
        - Move files and folders within Google Drive
        - Rename files and folders in Google Drive
        - Delete files and folders from Google Drive
    """

    def __init__(
            self,
            google_service: APIServiceLayer,
            llm: BaseChatModel,
            config: RunnableConfig = None,
    ):
        self._tools = [
            MoveFileTool(google_service),
            RenameFileTool(google_service),
            DeleteFileTool(google_service),
        ]

        self.agent = create_agent(
            name=self.name,
            model=llm,
            tools=self._tools,
            system_prompt=system_prompt.format(
                tools="\n".join([f"- {tool.name}: {tool.description}" for tool in self._tools])),
        )

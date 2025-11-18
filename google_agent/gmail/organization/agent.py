from textwrap import dedent

from google_client.api_service import APIServiceLayer
from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from .system_prompt import system_prompt
from .tools import ApplyLabelTool, RemoveLabelTool, CreateLabelTool, DeleteLabelTool, RenameLabelTool, DeleteEmailTool


class OrganizationAgent:
    name = "GmailOrganizationAgent"
    description = dedent("""
        Agent that can handle tasks related to organizing a gmail inbox.
        This includes applying, removing, creating, deleting, and renaming labels as well as deleting emails.
    """)

    def __init__(
            self,
            google_service: APIServiceLayer,
            llm: BaseChatModel,
            config: RunnableConfig = None,
    ):
        self._tools = [
            ApplyLabelTool(google_service),
            RemoveLabelTool(google_service),
            CreateLabelTool(google_service),
            DeleteLabelTool(google_service),
            RenameLabelTool(google_service),
            DeleteEmailTool(google_service)
        ]

        self.agent = create_agent(
            name=self.name,
            model=llm,
            tools=self._tools,
            system_prompt=system_prompt.format(
                tools="\n".join([f"- {tool.name}: {tool.description}" for tool in self._tools])),
        )

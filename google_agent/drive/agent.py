from textwrap import dedent

from google_client.api_service import APIServiceLayer
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from google_agent.shared.base_agent import BaseSupervisorAgent
from .organization.agent import OrganizationAgent
from .search_and_retrieval.agent import SearchAndRetrievalAgent
from .writer.agent import WriterAgent
from ..shared.tools import CurrentDateTimeTool


class DriveAgent(BaseSupervisorAgent):
    name: str = "DriveAgent"
    description: str = "A Google Drive expert that can handle complex tasks and queries related to Google Drive file management"

    def __init__(
            self,
            google_service: APIServiceLayer,
            llm: BaseChatModel,
            config: RunnableConfig = None,
    ):
        super().__init__(llm, google_service, config)

    def agents(self):
        return [
            OrganizationAgent(self.google_service, self.llm, self.config),
            SearchAndRetrievalAgent(self.google_service, self.llm, self.config),
            WriterAgent(self.google_service, self.llm, self.config)
        ]

    def tools(self):
        return [CurrentDateTimeTool(self.google_service.timezone)]

    def system_prompt(self):
        agent_description = []
        for agent in self.agents():
            agent_description.append(f"- {agent.name}: {agent.description}")

        tool_descriptions = []
        for tool in self.tools():
            tool_descriptions.append(f"- {tool.name}: {tool.description}")

        return dedent(
            f"""
            # Identity

            You are a team supervisor for a Google Drive team. You have access to following experts:
            {'\n'.join(agent_description)}

            AND the following tools:
            {'\n'.join(tool_descriptions)}

            # Instructions

            * Every question the user asks you is related to Google Drive files. If they ask you for any information that seems unrelated to files, try to find that information in their Drive.
            * At the end, summarize all actions taken and provide a detailed answer to the user's query

            ## Response Guidelines
            * Always include file IDs and/or folder IDs in your responses
            * Always include FULL FILE PATHS in your response for downloaded files
            * Always provide clear, organized results

            ## Context Awareness
            * Use the current_datetime_tool to get the current date and time when needed
            """
        )

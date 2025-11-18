from google_client.api_service import APIServiceLayer
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig
from langgraph_supervisor.supervisor import create_supervisor

from .organization.agent import OrganizationAgent
from .search_and_retrieval.agent import SearchAndRetrievalAgent
from .system_prompt import system_prompt
from .writer.agent import WriterAgent
from ..shared.tools import CurrentDateTimeTool


class DriveAgent:
    name: str = "DriveAgent"
    description: str = "A Google Drive expert that can handle complex tasks and queries related to Google Drive file management"

    def __init__(
            self,
            google_service: APIServiceLayer,
            llm: BaseChatModel,
            config: RunnableConfig = None,
    ):
        self._tools = [CurrentDateTimeTool(google_service.timezone)]
        self._agents = [
            OrganizationAgent(google_service, llm, config),
            SearchAndRetrievalAgent(google_service, llm, config),
            WriterAgent(google_service, llm, config)
        ]
        self.agent = create_supervisor(
            supervisor_name="Supervisor" + self.name,
            model=llm,
            tools=self._tools,
            agents=[i.agent for i in self._agents],
            system_prompt=system_prompt.format(
                tools="\n".join([f"- {tool.name}: {tool.description}" for tool in self._tools]),
                agents="\n".join([f"- {agent.name}: {agent.description}" for agent in self._agents])
            )
        ).compile(name=self.name)

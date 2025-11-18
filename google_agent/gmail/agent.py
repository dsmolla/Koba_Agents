from google_client.api_service import APIServiceLayer
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig
from langgraph_supervisor import create_supervisor

from google_agent.gmail.shared.email_cache import EmailCache
from .organization.agent import OrganizationAgent
from .search_and_retrieval.agent import SearchAndRetrievalAgent
from .summary_and_analytics.agent import SummaryAndAnalyticsAgent
from .system_prompt import system_prompt
from .writer.agent import WriterAgent
from ..shared.tools import CurrentDateTimeTool


class GmailAgent:
    name: str = "GmailAgent"
    description: str = "A Gmail expert that can handle complex tasks and queries related to Gmail"

    def __init__(
            self,
            google_service: APIServiceLayer,
            llm: BaseChatModel,
            config: RunnableConfig = None,
    ):
        self._email_cache = EmailCache()
        self._tools = [CurrentDateTimeTool(google_service.timezone)]
        self._agents = [
            OrganizationAgent(google_service, llm, config),
            SearchAndRetrievalAgent(google_service, llm, self._email_cache, config),
            SummaryAndAnalyticsAgent(google_service, llm, self._email_cache, config),
            WriterAgent(google_service, llm, config)
        ]
        self.agent = create_supervisor(
            supervisor_name="Supervisor" + self.name,
            model=llm,
            tools=self._tools,
            agents=[i.agent for i in self._agents],
            prompt=system_prompt.format(
                tools="\n".join([f"- {tool.name}: {tool.description}" for tool in self._tools]),
                agents="\n".join([f"- {agent.name}: {agent.description}" for agent in self._agents])
            )
        ).compile(name=self.name)

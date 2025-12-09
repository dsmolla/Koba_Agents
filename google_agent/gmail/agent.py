from google_agent.gmail.shared.email_cache import EmailCache
from google_agent.shared.base_agent import BaseSupervisorGoogleAgent
from google_agent.shared.tools import CurrentDateTimeTool
from .organization.agent import OrganizationAgent
from .search_and_retrieval.agent import SearchAndRetrievalAgent
from .summary_and_analytics.agent import SummaryAndAnalyticsAgent
from .writer.agent import WriterAgent


class GmailAgent(BaseSupervisorGoogleAgent):
    name: str = "GmailAgent"
    description: str = "A Gmail expert that can handle complex tasks and queries related to Gmail"

    def __init__(self, google_service, llm, config=None, download_folder=None):
        super().__init__(google_service, llm, config)
        self.download_folder = download_folder

    @property
    def tools(self):
        if self._tools is None:
            self._tools = [CurrentDateTimeTool(self.google_service.timezone)]
        return self._tools

    @property
    def sub_agents(self):
        if self._sub_agents is None:
            email_cache = EmailCache()
            self._sub_agents = [
                OrganizationAgent(
                    self.google_service,
                    self.llm,
                    self.config,
                ),
                SearchAndRetrievalAgent(
                    self.google_service,
                    self.llm,
                    email_cache,
                    self.config,
                    self.download_folder,
                ),
                SummaryAndAnalyticsAgent(
                    self.google_service,
                    self.llm,
                    email_cache,
                    self.config,
                ),
                WriterAgent(
                    self.google_service,
                    self.llm,
                    self.config,
                ),
            ]
        return self._sub_agents

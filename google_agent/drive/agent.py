from google_agent.shared.base_agent import BaseSupervisorGoogleAgent
from .organization.agent import OrganizationAgent
from .search_and_retrieval.agent import SearchAndRetrievalAgent
from .writer.agent import WriterAgent
from ..shared.tools import CurrentDateTimeTool


class DriveAgent(BaseSupervisorGoogleAgent):
    name: str = "DriveAgent"
    description: str = "A Google Drive expert that can handle complex tasks and queries related to Google Drive file management"

    @property
    def tools(self):
        if self._tools is None:
            self._tools = [CurrentDateTimeTool(self.google_service.timezone)]

        return self._tools

    @property
    def sub_agents(self):
        if self._sub_agents is None:
            self._sub_agents = [
                OrganizationAgent(
                    self.google_service,
                    self.llm,
                    self.config,
                ),
                SearchAndRetrievalAgent(
                    self.google_service,
                    self.llm,
                    self.config,
                ),
                WriterAgent(
                    self.google_service,
                    self.llm,
                    self.config,
                ),
            ]
        return self._sub_agents

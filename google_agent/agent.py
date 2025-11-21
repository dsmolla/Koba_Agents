from langgraph.checkpoint.memory import InMemorySaver

from google_agent.calendar.agent import CalendarAgent
from google_agent.drive.agent import DriveAgent
from google_agent.gmail.agent import GmailAgent
from google_agent.tasks.agent import TasksAgent
from .shared.base_agent import BaseSupervisorGoogleAgent
from .shared.tools import CurrentDateTimeTool


class GoogleAgent(BaseSupervisorGoogleAgent):
    name: str = "GoogleAgent"
    description: str = "A Google Workspace expert that can handle complex queries related to Gmail, Calendar, Tasks, and Drive"

    @property
    def tools(self):
        if self._tools is None:
            self._tools = [CurrentDateTimeTool(self.google_service.timezone)]
        return self._tools

    @property
    def checkpointer(self):
        return InMemorySaver()

    @property
    def sub_agents(self):
        if self._sub_agents is None:
            self._sub_agents = [
                GmailAgent(
                    self.google_service,
                    self.llm,
                    self.config,
                ),
                CalendarAgent(
                    self.google_service,
                    self.llm,
                    self.config,
                ),
                TasksAgent(
                    self.google_service,
                    self.llm,
                    self.config,
                ),
                DriveAgent(
                    self.google_service,
                    self.llm,
                    self.config,
                ),
            ]
        return self._sub_agents

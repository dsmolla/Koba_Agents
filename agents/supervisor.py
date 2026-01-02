from typing import override

from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langgraph.graph.state import CompiledStateGraph

from agents.google_calendar.agent import CalendarAgent
from agents.google_drive.agent import DriveAgent
from agents.gmail.agent import GmailAgent
from agents.google_tasks.agent import TasksAgent
from .shared.base_agent import BaseSupervisorGoogleAgent
from .shared.response import StructuredResponse
from .shared.tools import CurrentDateTimeTool


class GoogleAgent(BaseSupervisorGoogleAgent):
    name: str = "GoogleAgent"
    description: str = "A Google Workspace expert that can handle complex queries related to Gmail, Calendar, Tasks, and Drive"

    def __init__(self, google_service, llm, config=None, download_folder=None, checkpointer=None):
        super().__init__(google_service, llm, config)
        self._checkpointer = checkpointer
        self.download_folder = download_folder

    @property
    def tools(self):
        if self._tools is None:
            self._tools = [CurrentDateTimeTool(self.google_service.timezone)]
        return self._tools

    @property
    def checkpointer(self):
        return self._checkpointer

    @property
    def sub_agents(self):
        if self._sub_agents is None:
            self._sub_agents = [
                GmailAgent(
                    self.google_service,
                    self.llm,
                    self.config,
                    self.download_folder
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
                    self.download_folder
                ),
            ]
        return self._sub_agents

    @override
    @property
    def agent(self) -> CompiledStateGraph:
        if self._agent is None:
            self._agent = create_agent(
                name=self.name,
                model=self.llm,
                tools=self.tools + self.sub_agent_tools,
                system_prompt=self.system_prompt,
                checkpointer=self.checkpointer,
                response_format=ToolStrategy(StructuredResponse),
            )
        return self._agent

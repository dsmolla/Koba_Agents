from google_client.api_service import APIServiceLayer
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig
from langgraph_supervisor import create_supervisor

from google_agent.calendar.agent import CalendarAgent
from google_agent.drive.agent import DriveAgent
from google_agent.gmail.agent import GmailAgent
from google_agent.tasks.agent import TasksAgent
from .shared.tools import CurrentDateTimeTool
from .system_prompt import system_prompt
from langgraph.checkpoint.memory import InMemorySaver


class GoogleAgent:
    name: str = "GoogleAgent"
    description: str = "A Google Workspace expert that can handle complex queries related to Gmail, Calendar, Tasks, and Drive"

    def __init__(
            self,
            google_service: APIServiceLayer,
            llm: BaseChatModel,
            config: RunnableConfig = None
    ):
        self._tools = [CurrentDateTimeTool(google_service.timezone)]
        self._agents = [
            GmailAgent(google_service, llm, config),
            CalendarAgent(google_service, llm, config),
            TasksAgent(google_service, llm, config),
            DriveAgent(google_service, llm, config)
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
        ).compile(checkpointer=InMemorySaver(), name=self.name)

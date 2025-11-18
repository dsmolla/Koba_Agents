from google_client.api_service import APIServiceLayer
from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from .system_prompt import system_prompt
from .tools import ListCalendarsTool, CreateCalendarTool, DeleteCalendarTool, GetEventsTool, ListEventsTool, \
    CreateEventTool, DeleteEventTool, UpdateEventTool, FindFreeSlotsTool
from ..shared.tools import CurrentDateTimeTool


class CalendarAgent:
    name: str = "CalendarAgent"
    description: str = "A Calendar expert that can handle complex tasks and queries related to Google Calendar"

    def __init__(
            self,
            google_service: APIServiceLayer,
            llm: BaseChatModel,
            config: RunnableConfig = None,
    ):
        self._tools = [
            CurrentDateTimeTool(google_service.timezone),
            ListCalendarsTool(google_service),
            CreateCalendarTool(google_service),
            DeleteCalendarTool(google_service),
            GetEventsTool(google_service),
            ListEventsTool(google_service),
            CreateEventTool(google_service),
            DeleteEventTool(google_service),
            UpdateEventTool(google_service),
            FindFreeSlotsTool(google_service),
        ]

        self.agent = create_agent(
            name=self.name,
            model=llm,
            tools=self._tools,
            system_prompt=system_prompt.format(
                tools="\n".join([f"- {tool.name}: {tool.description}" for tool in self._tools])),
        )

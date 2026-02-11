from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import PromptTemplate

from agents.common.agent import BaseAgent
from .tools import *
from ..common.tools import CurrentDateTimeTool


class CalendarAgent(BaseAgent):
    name: str = "CalendarAgent"
    description: str = "A Google Calendar expert that can handle complex queries related to calendar management and event scheduling."

    def __init__(self, model: BaseChatModel):
        tools = [
            CurrentDateTimeTool(),
            ListCalendarsTool(),
            CreateCalendarTool(),
            DeleteCalendarTool(),
            GetEventsTool(),
            ListEventsTool(),
            CreateEventTool(),
            DeleteEventTool(),
            UpdateEventTool(),
            AddGoogleMeetsToEventTool(),
            FindFreeSlotsTool(),
        ]
        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")
        system_prompt = PromptTemplate.from_file(str(Path(__file__).parent / 'system_prompt.txt'))
        system_prompt = system_prompt.format(tools='\n'.join(tool_descriptions))

        super().__init__(model, tools, system_prompt)

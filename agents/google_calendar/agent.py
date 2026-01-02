from agents.shared.base_agent import BaseReactGoogleAgent
from .tools import *
from ..shared.tools import CurrentDateTimeTool


class CalendarAgent(BaseReactGoogleAgent):
    name: str = "CalendarAgent"
    description: str = "A Google Calendar expert that can handle complex queries related to calendar management and event scheduling."

    @property
    def tools(self):
        if self._tools is None:
            self._tools = [
                CurrentDateTimeTool(self.google_service.timezone),
                ListCalendarsTool(self.google_service),
                CreateCalendarTool(self.google_service),
                DeleteCalendarTool(self.google_service),
                GetEventsTool(self.google_service),
                ListEventsTool(self.google_service),
                CreateEventTool(self.google_service),
                DeleteEventTool(self.google_service),
                UpdateEventTool(self.google_service),
                FindFreeSlotsTool(self.google_service),
            ]
        return self._tools

from langchain_core.tools import BaseTool
from google_client.utils.datetime import current_datetime


class CurrentDateTimeTool(BaseTool):
    name: str = "current_datetime_tool"
    description: str = "Returns the current date and time."
    timezone: str

    def __init__(self, timezone: str = "UTC"):
        super().__init__(timezone=timezone)

    def _run(self) -> str:
        return current_datetime(self.timezone).strftime("%Y-%m-%dT%H:%M:%S")

    async def _arun(self, task_description: str) -> str:
        return current_datetime(self.timezone).strftime("%Y-%m-%dT%H:%M:%S")

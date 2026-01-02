from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from google_client.utils.datetime import current_datetime


class CurrentDateTimeTool(BaseTool):
    name: str = "current_datetime_tool"
    description: str = "Returns the current date and time."

    def _run(self) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(self, config: RunnableConfig) -> str:
        timezone = config["configurable"].get("user_timezone", "UTC")
        return current_datetime(timezone).strftime("%Y-%m-%dT%H:%M:%S")

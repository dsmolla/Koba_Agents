from typing import Annotated

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, InjectedToolArg
from langchain_core.callbacks import adispatch_custom_event
from google_client.utils.datetime import current_datetime


class CurrentDateTimeTool(BaseTool):
    name: str = "current_datetime_tool"
    description: str = "Returns the current date and time."

    def _run(self) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(self, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Checking Time...", "icon": "🕒"}
        )
        timezone = config["configurable"].get("timezone", "UTC")
        return current_datetime(timezone).strftime("%Y-%m-%dT%H:%M:%S")

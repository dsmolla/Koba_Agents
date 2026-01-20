from typing import Annotated
import logging

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, InjectedToolArg
from langchain_core.callbacks import adispatch_custom_event
from google_client.utils.datetime import current_datetime

logger = logging.getLogger(__name__)


class CurrentDateTimeTool(BaseTool):
    name: str = "current_datetime_tool"
    description: str = "Returns the current date and time."

    def _run(self) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(self, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        try:
            await adispatch_custom_event(
                "tool_status",
                {"text": "Checking Time...", "icon": "🕒"}
            )
            timezone = config["configurable"].get("timezone", "UTC")
            return current_datetime(timezone).strftime("%Y-%m-%dT%H:%M:%S")
        except Exception as e:
            logger.error(f"Error in CurrentDateTimeTool: {e}", exc_info=True)
            return "Unable to get current date and time due to internal error"

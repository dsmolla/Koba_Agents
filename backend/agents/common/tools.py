import json
import logging
from abc import ABC, abstractmethod
from typing import Annotated, Any

from google.auth.exceptions import RefreshError
from google_client.utils.datetime import current_datetime
from googleapiclient.errors import HttpError
from langchain_core.callbacks import adispatch_custom_event
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, InjectedToolArg

from core.exceptions import ProviderNotConnectedError

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


class BaseGoogleTool(BaseTool, ABC):
    """Base class for Google tools with common error handling."""

    provider_name: str = "Google"

    @abstractmethod
    async def _run_google_task(self, config: RunnableConfig, **kwargs) -> Any:
        pass

    async def _arun(self, config: Annotated[RunnableConfig, InjectedToolArg], **kwargs) -> str:
        try:
            result = await self._run_google_task(config, **kwargs)
            if isinstance(result, (dict, list)):
                return json.dumps(result)
            return str(result)

        except (ProviderNotConnectedError, RefreshError):
            return f"I currently don't have access to your {self.provider_name.lower()}. Please connect it from the settings page."

        except HttpError as e:
            if e.status_code == 403:
                return f"I currently don't have access to your {self.provider_name.lower()}. Please connect it from the settings page."
            logger.error(f"HTTP Error in {self.name}: {e}", exc_info=True)
            return f"An error occurred while accessing {self.provider_name}: {e.reason}"

        except Exception as e:
            logger.error(f"Error in {self.name}: {e}", exc_info=True)
            return f"Unable to complete the task due to an internal error."

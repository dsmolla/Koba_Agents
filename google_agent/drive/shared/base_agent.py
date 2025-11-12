from google_client.api_service import APIServiceLayer
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from google_agent.shared.base_agent import BaseAgent


class BaseDriveAgent(BaseAgent):
    """Base class for all Drive-specific agents"""

    def __init__(
        self,
        google_service: APIServiceLayer,
        llm: BaseChatModel,
        config: RunnableConfig = None
    ):
        self.google_service = google_service
        super().__init__(llm, config)
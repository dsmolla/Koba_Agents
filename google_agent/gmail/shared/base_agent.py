from abc import ABC
from typing import Optional

from google_client.api_service import APIServiceLayer
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from google_agent.shared.base_agent import BaseAgent


class BaseGmailAgent(BaseAgent, ABC):
    def __init__(
            self,
            google_service: APIServiceLayer,
            llm: BaseChatModel,
            config: Optional[RunnableConfig] = None
    ):
        self.google_service = google_service
        super().__init__(
            llm=llm,
            config=config
        )

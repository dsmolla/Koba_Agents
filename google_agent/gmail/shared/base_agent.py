from abc import ABC
from typing import Optional

from google_client.services.gmail.api_service import GmailApiService
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from google_agent.shared.base_agent import BaseAgent


class BaseGmailAgent(BaseAgent, ABC):
    def __init__(
            self,
            gmail_service: GmailApiService,
            llm: BaseChatModel,
            config: Optional[RunnableConfig] = None,
            print_steps: Optional[bool] = False,
    ):
        self.gmail_service = gmail_service
        super().__init__(
            llm=llm,
            config=config,
            print_steps=print_steps
        )

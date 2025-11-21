from textwrap import dedent
from typing import Optional

from google_client.api_service import APIServiceLayer
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from google_agent.gmail.shared.email_cache import EmailCache
from google_agent.shared.base_agent import BaseReactGoogleAgent
from google_agent.shared.tools import CurrentDateTimeTool
from .tools import SummarizeEmailsTool, ExtractFromEmailTool, ClassifyEmailTool


class SummaryAndAnalyticsAgent(BaseReactGoogleAgent):
    name = "SummaryAndAnalyticsAgent"
    description = dedent("""
        Specialized agent for summarizing and analyzing emails from a user's Gmail account with the following capabilities:
            - Summarize email threads or conversations (needs message_id or thread_id)
            - Extract key information from emails (needs message_id)
            - Classify emails into categories or tags (needs message_id)
    """)

    def __init__(
            self,
            google_service: APIServiceLayer,
            llm: BaseChatModel,
            email_cache: EmailCache,
            config: Optional[RunnableConfig] = None
    ):
        self.email_cache = email_cache
        super().__init__(google_service, llm, config)

    @property
    def tools(self):
        if self._tools is None:
            self._tools = [
                CurrentDateTimeTool(self.google_service.timezone),
                SummarizeEmailsTool(self.google_service, self.email_cache),
                ExtractFromEmailTool(self.google_service, self.email_cache),
                ClassifyEmailTool(self.google_service, self.email_cache),
            ]
        return self._tools

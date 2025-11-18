from typing import Optional

from google_client.api_service import APIServiceLayer
from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from google_agent.gmail.shared.email_cache import EmailCache
from .system_prompt import system_prompt
from .tools import SummarizeEmailsTool, ExtractFromEmailTool, ClassifyEmailTool
from ...shared.tools import CurrentDateTimeTool


class SummaryAndAnalyticsAgent:
    name = "GmailSummaryAndAnalyticsAgent"
    description = "Agent that can summarize, classify and extract information from emails in Gmail"

    def __init__(
            self,
            google_service: APIServiceLayer,
            llm: BaseChatModel,
            email_cache: EmailCache,
            config: Optional[RunnableConfig] = None
    ):
        self._tools = [
            CurrentDateTimeTool(google_service.timezone),
            SummarizeEmailsTool(google_service, email_cache),
            ExtractFromEmailTool(google_service, email_cache),
            ClassifyEmailTool(google_service, email_cache),
        ]

        self.agent = create_agent(
            name=self.name,
            model=llm,
            tools=self._tools,
            system_prompt=system_prompt.format(
                tools="\n".join([f"- {tool.name}: {tool.description}" for tool in self._tools])),
        )

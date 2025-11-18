from typing import Optional

from google_client.api_service import APIServiceLayer
from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from google_agent.gmail.shared.email_cache import EmailCache
from .system_prompt import system_prompt
from .tools import GetEmailTool, SearchEmailsTool, ListUserLabelsTool, DownloadAttachmentTool
from ...shared.tools import CurrentDateTimeTool


class SearchAndRetrievalAgent:
    name = "GmailRetrievalAgent"
    description = "Agent that specializes in searching, retrieving, and accessing Gmail emails, downloading attachments and listing user labels"

    def __init__(
            self,
            google_service: APIServiceLayer,
            llm: BaseChatModel,
            email_cache: EmailCache,
            config: Optional[RunnableConfig] = None
    ):
        self._tools = [
            CurrentDateTimeTool(google_service.timezone),
            GetEmailTool(google_service, email_cache),
            SearchEmailsTool(google_service, email_cache),
            DownloadAttachmentTool(google_service, email_cache),
            ListUserLabelsTool(google_service)
        ]

        self.agent = create_agent(
            name=self.name,
            model=llm,
            tools=self._tools,
            system_prompt=system_prompt.format(
                tools="\n".join([f"- {tool.name}: {tool.description}" for tool in self._tools])),
        )

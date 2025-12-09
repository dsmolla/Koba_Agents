from textwrap import dedent
from typing import Optional

from google_client.api_service import APIServiceLayer
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from google_agent.gmail.shared.email_cache import EmailCache
from google_agent.shared.base_agent import BaseReactGoogleAgent
from google_agent.shared.tools import CurrentDateTimeTool
from .tools import GetEmailTool, SearchEmailsTool, ListUserLabelsTool, DownloadAttachmentTool


class SearchAndRetrievalAgent(BaseReactGoogleAgent):
    name = "RetrievalAgent"
    description = dedent("""
        Specialized agent for searching and retrieving emails from a user's Gmail account with the following capabilities:
            - Search for emails based on various criteria
            - Retrieve email content (needs message_id)
            - Download email attachments (needs message_id)
            - List user labels
            
    """)

    def __init__(
            self,
            google_service: APIServiceLayer,
            llm: BaseChatModel,
            email_cache: EmailCache,
            config: Optional[RunnableConfig] = None,
            download_folder: Optional[str] = None
    ):
        self.email_cache = email_cache
        self.download_folder = download_folder
        super().__init__(google_service, llm, config)

    @property
    def tools(self):
        if self._tools is None:
            self._tools = [
                CurrentDateTimeTool(self.google_service.timezone),
                GetEmailTool(self.google_service, self.email_cache),
                SearchEmailsTool(self.google_service, self.email_cache),
                DownloadAttachmentTool(self.google_service, self.email_cache, self.download_folder),
                ListUserLabelsTool(self.google_service)
            ]
        return self._tools

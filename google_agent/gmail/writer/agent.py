from google_client.api_service import APIServiceLayer
from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from .system_prompt import system_prompt
from .tools import SendEmailTool, DraftEmailTool, ReplyEmailTool, ForwardEmailTool


class WriterAgent:
    name = "GmailWriterAgent"
    description = "Agent that can deals with sending, drafting, forwarding and replying of emails"

    def __init__(
            self,
            google_service: APIServiceLayer,
            llm: BaseChatModel,
            config: RunnableConfig = None,
    ):
        self._tools = [
            SendEmailTool(google_service),
            DraftEmailTool(google_service),
            ReplyEmailTool(google_service),
            ForwardEmailTool(google_service)
        ]

        self.agent = create_agent(
            name=self.name,
            model=llm,
            tools=self._tools,
            system_prompt=system_prompt.format(
                tools="\n".join([f"- {tool.name}: {tool.description}" for tool in self._tools])),
        )

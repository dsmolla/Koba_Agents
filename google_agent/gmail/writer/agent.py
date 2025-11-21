from textwrap import dedent

from google_agent.shared.base_agent import BaseReactGoogleAgent
from .tools import SendEmailTool, DraftEmailTool, ReplyEmailTool, ForwardEmailTool


class WriterAgent(BaseReactGoogleAgent):
    name = "WriterAgent"
    description = dedent("""
        Specialized agent for writing and drafting emails in Gmail with the following capabilities:
            - Send emails
            - Draft emails
            - Reply to emails (needs message_id)
            - Forward emails (needs message_id)
    """)

    @property
    def tools(self):
        if self._tools is None:
            self._tools = [
                SendEmailTool(self.google_service),
                DraftEmailTool(self.google_service),
                ReplyEmailTool(self.google_service),
                ForwardEmailTool(self.google_service)
            ]
        return self._tools

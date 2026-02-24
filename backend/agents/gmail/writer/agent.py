from pathlib import Path
from textwrap import dedent

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import PromptTemplate

from agents.common.agent import BaseAgent
from .tools import SendEmailTool, DraftEmailTool, ReplyEmailTool, ForwardEmailTool

_SYSTEM_PROMPT_TEMPLATE = Path(__file__).parent.joinpath('system_prompt.txt').read_text()


class WriterAgent(BaseAgent):
    name = "WriterAgent"
    description = dedent("""
        Specialized agent for writing and drafting emails in Gmail with the following capabilities:
            - Send emails
            - Draft emails
            - Reply to emails (needs message_id)
            - Forward emails (needs message_id)
    """)

    def __init__(self, model: BaseChatModel):
        tools = [
            SendEmailTool(),
            DraftEmailTool(),
            ReplyEmailTool(),
            ForwardEmailTool(),
        ]
        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")
        system_prompt = PromptTemplate.from_template(_SYSTEM_PROMPT_TEMPLATE).format(tools='\n'.join(tool_descriptions))

        super().__init__(model, tools, system_prompt)

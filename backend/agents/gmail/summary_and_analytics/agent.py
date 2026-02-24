from pathlib import Path
from textwrap import dedent

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import PromptTemplate

from agents.common.agent import BaseAgent
from agents.common.tools import CurrentDateTimeTool
from .tools import SummarizeEmailsTool, ExtractFromEmailTool, ClassifyEmailTool

_SYSTEM_PROMPT_TEMPLATE = Path(__file__).parent.joinpath('system_prompt.txt').read_text()


class SummaryAndAnalyticsAgent(BaseAgent):
    name = "SummaryAndAnalyticsAgent"
    description = dedent("""
        Specialized agent for summarizing and analyzing emails from a user's Gmail account with the following capabilities:
            - Summarize email threads or conversations (needs message_id or thread_id)
            - Extract key information from emails (needs message_id)
            - Classify emails into categories or tags (needs message_id)
    """)

    def __init__(self, model: BaseChatModel):
        tools = [
            CurrentDateTimeTool(),
            SummarizeEmailsTool(),
            ExtractFromEmailTool(),
            ClassifyEmailTool(),
        ]

        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")
        system_prompt = PromptTemplate.from_template(_SYSTEM_PROMPT_TEMPLATE).format(tools='\n'.join(tool_descriptions))

        super().__init__(model, tools, system_prompt)

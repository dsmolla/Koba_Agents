from pathlib import Path
from textwrap import dedent

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import PromptTemplate

from agents.shared.base_agent import BaseAgent
from agents.shared.tools import CurrentDateTimeTool
from .tools import SummarizeEmailsTool, ExtractFromEmailTool, ClassifyEmailTool


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
        system_prompt = PromptTemplate.from_file(str(Path(__file__).parent / 'system_prompt'))
        system_prompt = system_prompt.format(tools='\n'.join(tool_descriptions))

        super().__init__(model, tools, system_prompt)

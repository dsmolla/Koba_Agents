from pathlib import Path
from textwrap import dedent

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import PromptTemplate

from core.agent import BaseAgent
from agents.common.tools import CurrentDateTimeTool
from .tools import GetEmailTool, SearchEmailsTool, ListUserLabelsTool, DownloadAttachmentTool


class SearchAndRetrievalAgent(BaseAgent):
    name = "RetrievalAgent"
    description = dedent("""
        Specialized agent for searching and retrieving emails from a user's Gmail account with the following capabilities:
            - Search for emails based on various criteria
            - Retrieve email content (needs message_id)
            - Download email attachments (needs message_id)
            - List user labels
            
    """)

    def __init__(self, model: BaseChatModel):
        tools = [
            CurrentDateTimeTool(),
            GetEmailTool(),
            SearchEmailsTool(),
            DownloadAttachmentTool(),
            ListUserLabelsTool(),
        ]

        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")
        system_prompt = PromptTemplate.from_file(str(Path(__file__).parent / 'system_prompt.txt'))
        system_prompt = system_prompt.format(tools='\n'.join(tool_descriptions))

        super().__init__(model, tools, system_prompt)

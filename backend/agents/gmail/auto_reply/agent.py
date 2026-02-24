from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import PromptTemplate

from agents.common.agent import BaseAgent
from agents.common.tools import CurrentDateTimeTool
from agents.gmail.search_and_retrieval.tools import GetEmailTool, GetThreadDetailsTool
from agents.gmail.writer.tools import ReplyEmailTool, DraftEmailTool

_SYSTEM_PROMPT_TEMPLATE = Path(__file__).parent.joinpath('system_prompt.txt').read_text()


class GmailAutoReplyAgent(BaseAgent):
    name = "GmailAutoReplyAgent"
    description = "Specialized agent for automatically replying or creating drafts to a user's emails."

    def __init__(self, model: BaseChatModel):
        tools = [
            CurrentDateTimeTool(),
            GetEmailTool(),
            GetThreadDetailsTool(),
            ReplyEmailTool(),
            DraftEmailTool(),
        ]

        tool_descriptions = [f"- {tool.name}: {tool.description}" for tool in tools]
        system_prompt = PromptTemplate.from_template(_SYSTEM_PROMPT_TEMPLATE).format(tools='\n'.join(tool_descriptions))

        super().__init__(model, tools, system_prompt)

from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import PromptTemplate

from agents.common.agent import BaseAgent
from agents.common.tools import CurrentDateTimeTool
from agents.gmail.search_and_retrieval.tools import GetEmailTool, GetThreadDetailsTool
from agents.gmail.writer.tools import ReplyEmailTool, DraftEmailTool


class GmailAutoReplyAgent(BaseAgent):
    name = "GmailAutoReplyAgent"
    description = "Specialized agent for automatically replying or creating drafts to a user's emails."

    def __init__(self, model: BaseChatModel, rules: list[dict]):
        tools = [
            CurrentDateTimeTool(),
            GetEmailTool(),
            GetThreadDetailsTool(),
            ReplyEmailTool(),
            DraftEmailTool(),
        ]

        rules_text = "\n".join(
            f"{i}. When: {r['when_condition']}\n   Do: {r['do_action']}\n   Tone: {r['tone']}"
            for i, r in enumerate(rules, 1)
        )

        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")
        system_prompt = PromptTemplate.from_file(str(Path(__file__).parent / 'system_prompt.txt'))
        system_prompt = system_prompt.format(tools='\n'.join(tool_descriptions), rules=rules_text)

        super().__init__(model, tools, system_prompt)

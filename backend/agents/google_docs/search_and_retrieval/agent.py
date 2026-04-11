from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import PromptTemplate

from agents.common.agent import BaseAgent
from .tools import GetDocumentTool, GetDocumentTextTool, GetDocumentLinksTool

_SYSTEM_PROMPT_TEMPLATE = Path(__file__).parent.joinpath('system_prompt.txt').read_text()


class SearchAndRetrievalAgent(BaseAgent):
    name: str = "SearchAndRetrievalAgent"
    description: str = "Expert at reading and extracting data, urls, text, and metadata from Google Documents."

    def __init__(self, model: BaseChatModel):
        tools = [
            GetDocumentTool(),
            GetDocumentTextTool(),
            GetDocumentLinksTool()
        ]

        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")
        system_prompt = PromptTemplate.from_template(_SYSTEM_PROMPT_TEMPLATE).format(tools='\n'.join(tool_descriptions))

        super().__init__(model, tools, system_prompt)

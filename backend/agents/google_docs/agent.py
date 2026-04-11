from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import PromptTemplate

from agents.common.agent import BaseAgent, agent_to_tool
from .search_and_retrieval.agent import SearchAndRetrievalAgent
from .writer.agent import WriterAgent
from ..common.tools import CurrentDateTimeTool

_SYSTEM_PROMPT_TEMPLATE = Path(__file__).parent.joinpath('system_prompt.txt').read_text()


class DocsAgent(BaseAgent):
    name: str = "DocsAgent"
    description: str = "A Google Docs expert that can handle complex tasks, reading text, writing, formatting, and generating documents."

    def __init__(self, model: BaseChatModel):
        tools = [
            agent_to_tool(agent) for agent in [
                SearchAndRetrievalAgent(model),
                WriterAgent(model)
            ]
        ] + [CurrentDateTimeTool()]

        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")
        system_prompt = PromptTemplate.from_template(_SYSTEM_PROMPT_TEMPLATE).format(tools='\n'.join(tool_descriptions))

        super().__init__(model, tools, system_prompt)

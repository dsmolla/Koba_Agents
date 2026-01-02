from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import PromptTemplate

from core.agent import BaseAgent, agent_to_tool
from .organization.agent import OrganizationAgent
from .search_and_retrieval.agent import SearchAndRetrievalAgent
from .summary_and_analytics.agent import SummaryAndAnalyticsAgent
from .writer.agent import WriterAgent
from ..common.tools import CurrentDateTimeTool


class GmailAgent(BaseAgent):
    name: str = "GmailAgent"
    description: str = "A Gmail expert that can handle complex tasks and queries related to Gmail"

    def __init__(self, model: BaseChatModel):
        tools = [
            agent_to_tool(agent) for agent in [
                OrganizationAgent(model),
                SearchAndRetrievalAgent(model),
                SummaryAndAnalyticsAgent(model),
                WriterAgent(model),
            ]
        ] + [CurrentDateTimeTool()]


        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")
        system_prompt = PromptTemplate.from_file(str(Path(__file__).parent / 'system_prompt.txt'))
        system_prompt = system_prompt.format(tools='\n'.join(tool_descriptions))

        super().__init__(model, tools, system_prompt)

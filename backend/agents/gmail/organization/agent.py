from pathlib import Path
from textwrap import dedent

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import PromptTemplate

from agents.common.agent import BaseAgent
from .tools import ApplyLabelTool, RemoveLabelTool, CreateLabelTool, DeleteLabelTool, RenameLabelTool, DeleteEmailTool

_SYSTEM_PROMPT_TEMPLATE = Path(__file__).parent.joinpath('system_prompt.txt').read_text()


class OrganizationAgent(BaseAgent):
    name = "OrganizationAgent"
    description = dedent("""
        Specialized agent for managing Gmail labels and email deletion with the following capabilities:
            - Apply labels to emails (needs message_id)
            - Remove labels from emails (needs message_id)
            - Create new labels
            - Delete existing labels
            - Rename labels
            - Delete emails (needs message_id)
    """)

    def __init__(self, model: BaseChatModel):
        tools = [
            ApplyLabelTool(),
            RemoveLabelTool(),
            CreateLabelTool(),
            DeleteLabelTool(),
            RenameLabelTool(),
            DeleteEmailTool(),
        ]
        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")
        system_prompt = PromptTemplate.from_template(_SYSTEM_PROMPT_TEMPLATE).format(tools='\n'.join(tool_descriptions))

        super().__init__(model, tools, system_prompt)

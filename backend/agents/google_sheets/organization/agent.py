from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import PromptTemplate

from agents.common.agent import BaseAgent
from .tools import (
    CreateSpreadsheetTool, AddWorksheetTool, DeleteWorksheetTool,
    RenameWorksheetTool, DuplicateWorksheetTool
)

_SYSTEM_PROMPT_TEMPLATE = Path(__file__).parent.joinpath('system_prompt.txt').read_text()


class OrganizationAgent(BaseAgent):
    name: str = "OrganizationAgent"
    description: str = "Expert at structuring empty Spreadsheets and managing worksheets (tabs)."

    def __init__(self, model: BaseChatModel):
        tools = [
            CreateSpreadsheetTool(),
            AddWorksheetTool(),
            DeleteWorksheetTool(),
            RenameWorksheetTool(),
            DuplicateWorksheetTool()
        ]

        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")
        system_prompt = PromptTemplate.from_template(_SYSTEM_PROMPT_TEMPLATE).format(tools='\n'.join(tool_descriptions))

        super().__init__(model, tools, system_prompt)

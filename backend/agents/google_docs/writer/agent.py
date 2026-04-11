from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import PromptTemplate

from agents.common.agent import BaseAgent
from .tools import (
    CreateDocumentTool, InsertTextTool, DeleteTextTool, ReplaceAllTextTool,
    UpdateTextStyleTool, UpdateParagraphAlignmentTool, UpdateHeadingStyleTool,
    InsertPageBreakTool, InsertTableWithDataTool, BatchUpdateTool
)

_SYSTEM_PROMPT_TEMPLATE = Path(__file__).parent.joinpath('system_prompt.txt').read_text()


class WriterAgent(BaseAgent):
    name: str = "WriterAgent"
    description: str = "Expert at creating Google Documents, inserting text, formatting, and building tables."

    def __init__(self, model: BaseChatModel):
        tools = [
            CreateDocumentTool(),
            InsertTextTool(),
            DeleteTextTool(),
            ReplaceAllTextTool(),
            UpdateTextStyleTool(),
            UpdateParagraphAlignmentTool(),
            UpdateHeadingStyleTool(),
            InsertPageBreakTool(),
            InsertTableWithDataTool(),
            BatchUpdateTool()
        ]

        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")
        system_prompt = PromptTemplate.from_template(_SYSTEM_PROMPT_TEMPLATE).format(tools='\n'.join(tool_descriptions))

        super().__init__(model, tools, system_prompt)

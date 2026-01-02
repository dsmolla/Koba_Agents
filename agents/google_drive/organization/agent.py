from pathlib import Path
from textwrap import dedent

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import PromptTemplate

from core.agent import BaseAgent
from .tools import MoveFileTool, RenameFileTool, DeleteFileTool


class OrganizationAgent(BaseAgent):
    name: str = "OrganizationAgent"
    description: str = dedent("""
        Specialized agent for organizing Google Drive files and folders with the following capabilities:
            - Move files and folders (needs file_id/folder_id and folder_id)
            - Rename files and folders (needs file_id or folder_id)
            - Delete files and folders (needs file_id or folder_id)
    """)

    def __init__(self, model: BaseChatModel):
        tools = [
            MoveFileTool(),
            RenameFileTool(),
            DeleteFileTool(),
        ]
        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")
        system_prompt = PromptTemplate.from_file(str(Path(__file__).parent / 'system_prompt.txt'))
        system_prompt = system_prompt.format(tools='\n'.join(tool_descriptions))

        super().__init__(model, tools, system_prompt)

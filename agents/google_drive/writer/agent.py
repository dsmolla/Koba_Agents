from pathlib import Path
from textwrap import dedent

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import PromptTemplate

from core.agent import BaseAgent
from .tools import UploadFileTool, CreateFolderTool, ShareFileTool


class WriterAgent(BaseAgent):
    name: str = "WriterAgent"
    description: str = dedent("""
        Specialized agent for managing Google Drive files and folders with the following capabilities:
            - Upload files to Google Drive (needs file path and folder_id)
            - Create folders in Google Drive (needs folder name and optional parent folder_id)
            - Share files and folders with other users (needs file_id/folder_id)
    """)

    def __init__(self, model: BaseChatModel):
        tools = [
            UploadFileTool(),
            CreateFolderTool(),
            ShareFileTool(),
        ]

        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")
        system_prompt = PromptTemplate.from_file(str(Path(__file__).parent / 'system_prompt.txt'))
        system_prompt = system_prompt.format(tools='\n'.join(tool_descriptions))

        super().__init__(model, tools, system_prompt)

from pathlib import Path
from textwrap import dedent

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import PromptTemplate

from agents.common.agent import BaseAgent
from .tools import SearchFilesTool, GetFileTool, DownloadFileTool, ListFolderContentsTool, GetPermissionsTool
from ...common.tools import CurrentDateTimeTool

_SYSTEM_PROMPT_TEMPLATE = Path(__file__).parent.joinpath('system_prompt.txt').read_text()


class SearchAndRetrievalAgent(BaseAgent):
    name: str = "SearchAndRetrievalAgent"
    description: str = dedent("""
        Specialized agent for searching and retrieving Google Drive files and folders with the following capabilities:
            - Search for files and folders based on various criteria
            - Retrieve file/folder metadata and content (needs file_id or folder_id)
            - Download files (needs file_id)
            - List contents of folders (needs folder_id)
            - Get sharing permissions of files and folders (needs file_id or folder_id)
    """)

    def __init__(self, model: BaseChatModel):
        tools = [
            CurrentDateTimeTool(),
            SearchFilesTool(),
            GetFileTool(),
            DownloadFileTool(),
            ListFolderContentsTool(),
            GetPermissionsTool(),
        ]

        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")
        system_prompt = PromptTemplate.from_template(_SYSTEM_PROMPT_TEMPLATE).format(tools='\n'.join(tool_descriptions))

        super().__init__(model, tools, system_prompt)

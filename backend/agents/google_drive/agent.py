from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import PromptTemplate

from agents.common.agent import BaseAgent
from agents.common.tools import CurrentDateTimeTool
from agents.gmail.search_and_retrieval.tools import SaveAttachmentToDriveTool
from .organization.tools import MoveFileTool, RenameFileTool, DeleteFileTool
from .search_and_retrieval.tools import (
    SearchFilesTool, GetFileTool, DownloadFileTool, ListFolderContentsTool, GetPermissionsTool
)
from .writer.tools import UploadFileTool, CreateFolderTool, ShareFileTool

_SYSTEM_PROMPT_TEMPLATE = Path(__file__).parent.joinpath('system_prompt.txt').read_text()


class DriveAgent(BaseAgent):
    name: str = "DriveAgent"
    description: str = (
        "A Google Drive expert that handles file management including search, upload, organize, and sharing. "
        "Can also save Gmail email attachments directly to Drive — pass message_id and optionally attachment_id and folder_id."
    )

    def __init__(self, model: BaseChatModel):
        tools = [
            CurrentDateTimeTool(),
            # Search & Retrieval
            SearchFilesTool(),
            GetFileTool(),
            DownloadFileTool(),
            ListFolderContentsTool(),
            GetPermissionsTool(),
            # Organization
            MoveFileTool(),
            RenameFileTool(),
            DeleteFileTool(),
            # Writing
            UploadFileTool(),
            CreateFolderTool(),
            ShareFileTool(),
            SaveAttachmentToDriveTool(),
        ]

        tool_descriptions = [f"- {tool.name}: {tool.description}" for tool in tools]
        system_prompt = PromptTemplate.from_template(_SYSTEM_PROMPT_TEMPLATE).format(
            tools='\n'.join(tool_descriptions)
        )

        super().__init__(model, tools, system_prompt)

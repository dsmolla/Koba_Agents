from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import PromptTemplate

from agents.common.agent import BaseAgent
from agents.common.tools import CurrentDateTimeTool
from .organization.tools import (
    ApplyLabelTool, RemoveLabelTool, CreateLabelTool, DeleteLabelTool, RenameLabelTool, DeleteEmailTool
)
from .search_and_retrieval.tools import (
    GetEmailTool, GetThreadDetailsTool, SearchEmailsTool, DownloadAttachmentTool, ListUserLabelsTool
)
from .summary_and_analytics.tools import SummarizeEmailsTool, ExtractFromEmailTool, ClassifyEmailTool
from .writer.tools import SendEmailTool, DraftEmailTool, ReplyEmailTool, ForwardEmailTool

_SYSTEM_PROMPT_TEMPLATE = Path(__file__).parent.joinpath('system_prompt.txt').read_text()


class GmailAgent(BaseAgent):
    name: str = "GmailAgent"
    description: str = (
        "A Gmail expert that handles all email tasks including search, summarization, labels, and writing. "
        "Can also send, draft, and reply to emails with Google Drive files attached — pass drive_file_ids for Drive attachments."
    )

    def __init__(self, model: BaseChatModel):
        tools = [
            CurrentDateTimeTool(),
            # Search & Retrieval
            SearchEmailsTool(),
            GetEmailTool(),
            GetThreadDetailsTool(),
            DownloadAttachmentTool(),
            ListUserLabelsTool(),
            # Summary & Analytics
            SummarizeEmailsTool(),
            ExtractFromEmailTool(),
            ClassifyEmailTool(),
            # Organization
            ApplyLabelTool(),
            RemoveLabelTool(),
            CreateLabelTool(),
            DeleteLabelTool(),
            RenameLabelTool(),
            DeleteEmailTool(),
            # Writing
            SendEmailTool(),
            DraftEmailTool(),
            ReplyEmailTool(),
            ForwardEmailTool(),
        ]

        tool_descriptions = [f"- {tool.name}: {tool.description}" for tool in tools]
        system_prompt = PromptTemplate.from_template(_SYSTEM_PROMPT_TEMPLATE).format(
            tools='\n'.join(tool_descriptions)
        )

        super().__init__(model, tools, system_prompt)

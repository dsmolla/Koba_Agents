from typing import Optional, Annotated, List, Dict, Any
from pydantic import BaseModel, Field
import json
import logging
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import ArgsSchema, InjectedToolArg
from langchain_core.callbacks import adispatch_custom_event

from agents.common.tools import BaseGoogleTool
from core.auth import get_docs_service

logger = logging.getLogger(__name__)


class CreateDocumentInput(BaseModel):
    title: str = Field(description="The title of the new Google Document")


class CreateDocumentTool(BaseGoogleTool):
    name: str = "create_document"
    description: str = "Create a new, blank Google Document."
    args_schema: ArgsSchema = CreateDocumentInput

    def _run(self, title: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, title: str) -> str:
        await adispatch_custom_event("tool_status", {"text": "Creating Document...", "icon": "📝"})
        docs = await get_docs_service(config)
        doc = await docs.create_document(title)
        return f"Document created successfully. document_id: {doc.document_id}"


class InsertTextInput(BaseModel):
    document_id: str = Field(description="The ID of the document")
    text: str = Field(description="The text to insert")
    index: int = Field(default=1, description="The 1-based index where the text will be inserted")


class InsertTextTool(BaseGoogleTool):
    name: str = "insert_text"
    description: str = "Insert text at a specific index in a Google Document."
    args_schema: ArgsSchema = InsertTextInput

    def _run(self, document_id: str, text: str, index: int, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, document_id: str, text: str, index: int) -> str:
        await adispatch_custom_event("tool_status", {"text": "Inserting Text...", "icon": "✍️"})
        docs = await get_docs_service(config)
        success = await docs.insert_text(document_id, text, index)
        return "Success" if success else "Failed to insert text."


class DeleteTextInput(BaseModel):
    document_id: str = Field(description="The ID of the document")
    start_index: int = Field(description="The starting half-open index (inclusive)")
    end_index: int = Field(description="The ending half-open index (exclusive)")


class DeleteTextTool(BaseGoogleTool):
    name: str = "delete_text"
    description: str = "Delete text between start_index and end_index."
    args_schema: ArgsSchema = DeleteTextInput

    def _run(self, document_id: str, start_index: int, end_index: int, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, document_id: str, start_index: int, end_index: int) -> str:
        await adispatch_custom_event("tool_status", {"text": "Deleting Text...", "icon": "🗑️"})
        docs = await get_docs_service(config)
        success = await docs.delete_text(document_id, start_index, end_index)
        return "Success" if success else "Failed to delete text."


class ReplaceAllTextInput(BaseModel):
    document_id: str = Field(description="The ID of the document")
    contains_text: str = Field(description="The exact substring to locate and replace")
    replace_text: str = Field(description="The new text string to inject")
    match_case: bool = Field(default=True, description="If True, only replaces exact capitalization matches")


class ReplaceAllTextTool(BaseGoogleTool):
    name: str = "replace_all_text"
    description: str = "Replace all instances of a specific substring with new text."
    args_schema: ArgsSchema = ReplaceAllTextInput

    def _run(self, document_id: str, contains_text: str, replace_text: str, match_case: bool, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, document_id: str, contains_text: str, replace_text: str, match_case: bool) -> str:
        await adispatch_custom_event("tool_status", {"text": "Replacing Text...", "icon": "🔄"})
        docs = await get_docs_service(config)
        success = await docs.replace_all_text(document_id, contains_text, replace_text, match_case)
        return "Success" if success else "Failed to replace text."


class UpdateTextStyleInput(BaseModel):
    document_id: str = Field(description="The ID of the document")
    start_index: int = Field(description="The starting index (inclusive)")
    end_index: int = Field(description="The ending index (exclusive)")
    bold: Optional[bool] = Field(default=None, description="Set to True to bold the text, False to unbold")
    italic: Optional[bool] = Field(default=None, description="Set to True to italicize the text")
    font_family: Optional[str] = Field(default=None, description="String name of the Google Font to apply")
    font_size: Optional[int] = Field(default=None, description="The font size in points (e.g. 12)")


class UpdateTextStyleTool(BaseGoogleTool):
    name: str = "update_text_style"
    description: str = "Update the stylistic properties (bold, italic, font, size) of text within a specific range."
    args_schema: ArgsSchema = UpdateTextStyleInput

    def _run(self, document_id: str, start_index: int, end_index: int, config: Annotated[RunnableConfig, InjectedToolArg], **kwargs) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, document_id: str, start_index: int, end_index: int, **kwargs) -> str:
        await adispatch_custom_event("tool_status", {"text": "Formatting Text...", "icon": "🎨"})
        docs = await get_docs_service(config)
        success = await docs.update_text_style(document_id, start_index, end_index, **kwargs)
        return "Success" if success else "Failed to update text style."


class UpdateParagraphAlignmentInput(BaseModel):
    document_id: str = Field(description="The ID of the document")
    start_index: int = Field(description="The starting index (inclusive)")
    end_index: int = Field(description="The ending index (exclusive)")
    alignment: str = Field(description='The alignment type ("START", "CENTER", "END", "JUSTIFIED")')


class UpdateParagraphAlignmentTool(BaseGoogleTool):
    name: str = "update_paragraph_alignment"
    description: str = "Update the alignment layout of paragraphs overlapping the specified range."
    args_schema: ArgsSchema = UpdateParagraphAlignmentInput

    def _run(self, document_id: str, start_index: int, end_index: int, alignment: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, document_id: str, start_index: int, end_index: int, alignment: str) -> str:
        await adispatch_custom_event("tool_status", {"text": "Aligning Text...", "icon": "📑"})
        docs = await get_docs_service(config)
        success = await docs.update_paragraph_alignment(document_id, start_index, end_index, alignment)
        return "Success" if success else "Failed to update paragraph alignment."


class UpdateHeadingStyleInput(BaseModel):
    document_id: str = Field(description="The ID of the document")
    start_index: int = Field(description="The starting index (inclusive)")
    end_index: int = Field(description="The ending index (exclusive)")
    heading_id: str = Field(description='A valid Docs heading type ("NORMAL_TEXT", "HEADING_1", etc.)')


class UpdateHeadingStyleTool(BaseGoogleTool):
    name: str = "update_heading_style"
    description: str = "Change the targeted paragraph style to a predefined heading size."
    args_schema: ArgsSchema = UpdateHeadingStyleInput

    def _run(self, document_id: str, start_index: int, end_index: int, heading_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, document_id: str, start_index: int, end_index: int, heading_id: str) -> str:
        await adispatch_custom_event("tool_status", {"text": "Updating Heading...", "icon": "📌"})
        docs = await get_docs_service(config)
        success = await docs.update_heading_style(document_id, start_index, end_index, heading_id)
        return "Success" if success else "Failed to update heading style."


class InsertPageBreakInput(BaseModel):
    document_id: str = Field(description="The ID of the document")
    index: int = Field(description="The 1-based index where the page break is inserted")


class InsertPageBreakTool(BaseGoogleTool):
    name: str = "insert_page_break"
    description: str = "Force a page break at the specific index."
    args_schema: ArgsSchema = InsertPageBreakInput

    def _run(self, document_id: str, index: int, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, document_id: str, index: int) -> str:
        await adispatch_custom_event("tool_status", {"text": "Inserting Page Break...", "icon": "📄"})
        docs = await get_docs_service(config)
        success = await docs.insert_page_break(document_id, index)
        return "Success" if success else "Failed to insert page break."


class InsertTableWithDataInput(BaseModel):
    document_id: str = Field(description="The ID of the document")
    index: int = Field(description="The starting index where the new table should be inserted")
    data: List[List[str]] = Field(description="A 2D list array mapping directly to the table layout")


class InsertTableWithDataTool(BaseGoogleTool):
    name: str = "insert_table_with_data"
    description: str = "Create a table and automatically fill it with a 2D data list at a given index."
    args_schema: ArgsSchema = InsertTableWithDataInput

    def _run(self, document_id: str, index: int, data: List[List[str]], config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, document_id: str, index: int, data: List[List[str]]) -> str:
        await adispatch_custom_event("tool_status", {"text": "Inserting Table...", "icon": "▦"})
        docs = await get_docs_service(config)
        success = await docs.insert_table_with_data(document_id, index, data)
        return "Success" if success else "Failed to insert table with data."


class BatchUpdateInput(BaseModel):
    document_id: str = Field(description="The ID of the document")
    requests: List[Dict[str, Any]] = Field(description="A list of dict payloads representing Google Docs API requests")


class BatchUpdateTool(BaseGoogleTool):
    name: str = "batch_update"
    description: str = "Execute a custom batchUpdate mapping directly to raw JSON Google Docs API requests."
    args_schema: ArgsSchema = BatchUpdateInput

    def _run(self, document_id: str, requests: List[Dict[str, Any]], config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, document_id: str, requests: List[Dict[str, Any]]) -> str:
        await adispatch_custom_event("tool_status", {"text": "Batch Updating...", "icon": "⚙️"})
        docs = await get_docs_service(config)
        try:
            result = await docs.batch_update(document_id, requests)
            return json.dumps(result)
        except Exception as e:
            return f"Failed: {str(e)}"

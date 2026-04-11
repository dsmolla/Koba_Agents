from typing import Optional, Annotated, List, Dict
from pydantic import BaseModel, Field
import json
import logging
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import ArgsSchema, InjectedToolArg
from langchain_core.callbacks import adispatch_custom_event

from agents.common.tools import BaseGoogleTool
from core.auth import get_docs_service

logger = logging.getLogger(__name__)


class GetDocumentInput(BaseModel):
    document_id: str = Field(description="The ID of the Google Document to fetch.")


class GetDocumentTool(BaseGoogleTool):
    name: str = "get_document"
    description: str = "Fetch a Google Document's metadata and structured formatting details by its ID."
    args_schema: ArgsSchema = GetDocumentInput

    def _run(self, document_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, document_id: str) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Fetching Document...", "icon": "📄"}
        )
        docs = await get_docs_service(config)
        doc = await docs.get_document(document_id)
        if hasattr(doc, 'model_dump_json'):
            return doc.model_dump_json()
        return str(doc)


class GetDocumentTextInput(BaseModel):
    document_id: str = Field(description="The ID of the Google Document to read.")


class GetDocumentTextTool(BaseGoogleTool):
    name: str = "get_document_text"
    description: str = "Read the entire raw text contents of a Google Document."
    args_schema: ArgsSchema = GetDocumentTextInput

    def _run(self, document_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, document_id: str) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Reading Document Text...", "icon": "📖"}
        )
        docs = await get_docs_service(config)
        text = await docs.get_document_text(document_id)
        return text


class GetDocumentLinksInput(BaseModel):
    document_id: str = Field(description="The ID of the Google Document to parse for links.")


class GetDocumentLinksTool(BaseGoogleTool):
    name: str = "get_document_links"
    description: str = "Extract all URLs and their anchor text from a Google Document."
    args_schema: ArgsSchema = GetDocumentLinksInput

    def _run(self, document_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, document_id: str) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Extracting Links...", "icon": "🔗"}
        )
        docs = await get_docs_service(config)
        links = await docs.get_document_links(document_id)
        return json.dumps(links)

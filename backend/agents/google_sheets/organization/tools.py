from typing import Optional, Annotated, List, Dict, Any
from pydantic import BaseModel, Field
import json
import logging
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import ArgsSchema, InjectedToolArg
from langchain_core.callbacks import adispatch_custom_event

from agents.common.tools import BaseGoogleTool
from core.auth import get_sheets_service

logger = logging.getLogger(__name__)


class CreateSpreadsheetInput(BaseModel):
    title: str = Field(description="The title string of the new Google Spreadsheet.")


class CreateSpreadsheetTool(BaseGoogleTool):
    name: str = "create_spreadsheet"
    description: str = "Create a new, blank Google Spreadsheet."
    args_schema: ArgsSchema = CreateSpreadsheetInput

    def _run(self, title: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, title: str) -> str:
        await adispatch_custom_event("tool_status", {"text": "Creating Spreadsheet...", "icon": "📊"})
        sheets = await get_sheets_service(config)
        sheet = await sheets.create_spreadsheet(title)
        return f"Spreadsheet created successfully. spreadsheet_id: {sheet.spreadsheet_id}"


class AddWorksheetInput(BaseModel):
    spreadsheet_id: str = Field(description="The ID of the Google Spreadsheet.")
    title: str = Field(description="Title of the new worksheet tab.")
    rows: int = Field(default=1000, description="Number of rows")
    cols: int = Field(default=26, description="Number of columns")


class AddWorksheetTool(BaseGoogleTool):
    name: str = "add_worksheet"
    description: str = "Add a new worksheet tab to a spreadsheet."
    args_schema: ArgsSchema = AddWorksheetInput

    def _run(self, spreadsheet_id: str, title: str, rows: int, cols: int, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, spreadsheet_id: str, title: str, rows: int, cols: int) -> str:
        await adispatch_custom_event("tool_status", {"text": "Adding Worksheet...", "icon": "➕"})
        sheets = await get_sheets_service(config)
        success = await sheets.add_worksheet(spreadsheet_id, title, rows, cols)
        return "Success" if success else "Failed to add worksheet."


class DeleteWorksheetInput(BaseModel):
    spreadsheet_id: str = Field(description="The ID of the Google Spreadsheet.")
    sheet_id: int = Field(description="The numeric sheet_id of the tab to delete.")


class DeleteWorksheetTool(BaseGoogleTool):
    name: str = "delete_worksheet"
    description: str = "Delete a worksheet tab."
    args_schema: ArgsSchema = DeleteWorksheetInput

    def _run(self, spreadsheet_id: str, sheet_id: int, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, spreadsheet_id: str, sheet_id: int) -> str:
        await adispatch_custom_event("tool_status", {"text": "Deleting Worksheet...", "icon": "🗑️"})
        sheets = await get_sheets_service(config)
        success = await sheets.delete_worksheet(spreadsheet_id, sheet_id)
        return "Success" if success else "Failed to delete worksheet."


class RenameWorksheetInput(BaseModel):
    spreadsheet_id: str = Field(description="The ID of the Google Spreadsheet.")
    sheet_id: int = Field(description="The numeric sheet_id of the tab to rename.")
    new_title: str = Field(description="The new title line for the tab.")


class RenameWorksheetTool(BaseGoogleTool):
    name: str = "rename_worksheet"
    description: str = "Rename an existing worksheet tab."
    args_schema: ArgsSchema = RenameWorksheetInput

    def _run(self, spreadsheet_id: str, sheet_id: int, new_title: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, spreadsheet_id: str, sheet_id: int, new_title: str) -> str:
        await adispatch_custom_event("tool_status", {"text": "Renaming Worksheet...", "icon": "✏️"})
        sheets = await get_sheets_service(config)
        success = await sheets.rename_worksheet(spreadsheet_id, sheet_id, new_title)
        return "Success" if success else "Failed to rename worksheet."


class DuplicateWorksheetInput(BaseModel):
    spreadsheet_id: str = Field(description="The ID of the Google Spreadsheet.")
    source_sheet_id: int = Field(description="The numeric sheet_id of the tab to duplicate.")
    new_title: str = Field(description="The new title line for the cloned tab.")


class DuplicateWorksheetTool(BaseGoogleTool):
    name: str = "duplicate_worksheet"
    description: str = "Duplicate an existing worksheet tab into a new one."
    args_schema: ArgsSchema = DuplicateWorksheetInput

    def _run(self, spreadsheet_id: str, source_sheet_id: int, new_title: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, spreadsheet_id: str, source_sheet_id: int, new_title: str) -> str:
        await adispatch_custom_event("tool_status", {"text": "Duplicating Worksheet...", "icon": "📋"})
        sheets = await get_sheets_service(config)
        success = await sheets.duplicate_worksheet(spreadsheet_id, source_sheet_id, new_title)
        return "Success" if success else "Failed to duplicate worksheet."

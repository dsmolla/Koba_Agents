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


class GetSpreadsheetInput(BaseModel):
    spreadsheet_id: str = Field(description="The ID of the Google Spreadsheet to fetch.")


class GetSpreadsheetTool(BaseGoogleTool):
    name: str = "get_spreadsheet"
    description: str = "Fetch a Google Spreadsheet's metadata, properties, and list of its worksheets by spreadsheet_id."
    args_schema: ArgsSchema = GetSpreadsheetInput

    def _run(self, spreadsheet_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, spreadsheet_id: str) -> str:
        await adispatch_custom_event("tool_status", {"text": "Fetching Spreadsheet...", "icon": "📊"})
        sheets = await get_sheets_service(config)
        sheet = await sheets.get_spreadsheet(spreadsheet_id)
        if hasattr(sheet, 'model_dump_json'):
            return sheet.model_dump_json()
        return str(sheet)


class GetValuesInput(BaseModel):
    spreadsheet_id: str = Field(description="The ID of the Google Spreadsheet.")
    range_name: str = Field(description='A1 notation target range (e.g., "Sheet1!A1:C10").')
    as_dicts: bool = Field(default=False, description="If True, parses the range so the first row acts as dictionary keys for subsequent rows.")


class GetValuesTool(BaseGoogleTool):
    name: str = "get_values"
    description: str = "Retrieve raw grid values from a spreadsheet range, optionally mapped as a list of dictionaries."
    args_schema: ArgsSchema = GetValuesInput

    def _run(self, spreadsheet_id: str, range_name: str, config: Annotated[RunnableConfig, InjectedToolArg], as_dicts: bool = False) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, spreadsheet_id: str, range_name: str, as_dicts: bool = False) -> str:
        await adispatch_custom_event("tool_status", {"text": "Reading Values...", "icon": "🔍"})
        sheets = await get_sheets_service(config)
        if as_dicts:
            data = await sheets.get_values_as_dicts(spreadsheet_id, range_name)
            return json.dumps(data)
        else:
            data = await sheets.get_values(spreadsheet_id, range_name)
            if hasattr(data, 'model_dump_json'):
                return data.model_dump_json()
            return str(data)


class FindValueInput(BaseModel):
    spreadsheet_id: str = Field(description="The ID of the Google Spreadsheet.")
    range_name: str = Field(description='A1 notation bound where to search.')
    search_string: str = Field(description="The substring to exact-match against cell values.")


class FindValueTool(BaseGoogleTool):
    name: str = "find_value"
    description: str = "Search an A1 notation range for a specific string and return its relative row and column index."
    args_schema: ArgsSchema = FindValueInput

    def _run(self, spreadsheet_id: str, range_name: str, search_string: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, spreadsheet_id: str, range_name: str, search_string: str) -> str:
        await adispatch_custom_event("tool_status", {"text": "Finding Value...", "icon": "🕵️"})
        sheets = await get_sheets_service(config)
        result = await sheets.find_value(spreadsheet_id, range_name, search_string)
        if result is None:
            return "Value not found."
        return f"Found at relative row index: {result[0]}, column index: {result[1]}"

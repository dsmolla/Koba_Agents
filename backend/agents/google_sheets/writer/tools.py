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


class UpdateValuesInput(BaseModel):
    spreadsheet_id: str = Field(description="The ID of the spreadsheet")
    range_name: str = Field(description="A1 notation range to update")
    values: List[List[str]] = Field(description="2D array of strings to write")


class UpdateValuesTool(BaseGoogleTool):
    name: str = "update_values"
    description: str = "Overwrite cells in a given bounds with a 2D array."
    args_schema: ArgsSchema = UpdateValuesInput

    def _run(self, spreadsheet_id: str, range_name: str, values: List[List[str]], config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError()

    async def _run_google_task(self, config: RunnableConfig, spreadsheet_id: str, range_name: str, values: List[List[str]]) -> str:
        await adispatch_custom_event("tool_status", {"text": "Updating Values...", "icon": "✍️"})
        sheets = await get_sheets_service(config)
        success = await sheets.update_values(spreadsheet_id, range_name, values)
        return "Success" if success else "Failed to update values."


class AppendValuesInput(BaseModel):
    spreadsheet_id: str = Field(description="The ID of the spreadsheet")
    range_name: str = Field(description="A1 notation target table bound")
    values: List[List[str]] = Field(description="2D array of strings to append")


class AppendValuesTool(BaseGoogleTool):
    name: str = "append_values"
    description: str = "Append a 2D array of values to the bottom of an existing data range."
    args_schema: ArgsSchema = AppendValuesInput

    def _run(self, spreadsheet_id: str, range_name: str, values: List[List[str]], config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError()

    async def _run_google_task(self, config: RunnableConfig, spreadsheet_id: str, range_name: str, values: List[List[str]]) -> str:
        await adispatch_custom_event("tool_status", {"text": "Appending Values...", "icon": "⬇️"})
        sheets = await get_sheets_service(config)
        success = await sheets.append_values(spreadsheet_id, range_name, values)
        return "Success" if success else "Failed to append values."


class AppendValuesFromDictsInput(BaseModel):
    spreadsheet_id: str = Field(description="The ID of the spreadsheet")
    range_name: str = Field(description="A1 notation target table bound starting with the header row")
    data: List[Dict[str, Any]] = Field(description="List of key-value payloads to append matched by headers")


class AppendValuesFromDictsTool(BaseGoogleTool):
    name: str = "append_values_from_dicts"
    description: str = "Append structural data by mapping a list of dicts to the sheet's existing headers."
    args_schema: ArgsSchema = AppendValuesFromDictsInput

    def _run(self, spreadsheet_id: str, range_name: str, data: List[Dict[str, Any]], config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError()

    async def _run_google_task(self, config: RunnableConfig, spreadsheet_id: str, range_name: str, data: List[Dict[str, Any]]) -> str:
        await adispatch_custom_event("tool_status", {"text": "Appending Dicts...", "icon": "⬇️"})
        sheets = await get_sheets_service(config)
        success = await sheets.append_values_from_dicts(spreadsheet_id, range_name, data)
        return "Success" if success else "Failed to append dicts."


class ClearValuesInput(BaseModel):
    spreadsheet_id: str = Field(description="The ID of the spreadsheet")
    range_name: str = Field(description="A1 notation target table bound")


class ClearValuesTool(BaseGoogleTool):
    name: str = "clear_values"
    description: str = "Clear all cell values in a range."
    args_schema: ArgsSchema = ClearValuesInput

    def _run(self, spreadsheet_id: str, range_name: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError()

    async def _run_google_task(self, config: RunnableConfig, spreadsheet_id: str, range_name: str) -> str:
        await adispatch_custom_event("tool_status", {"text": "Clearing Range...", "icon": "🧹"})
        sheets = await get_sheets_service(config)
        success = await sheets.clear_values(spreadsheet_id, range_name)
        return "Success" if success else "Failed to clear."


class FormatRangeInput(BaseModel):
    spreadsheet_id: str = Field(description="The ID of the spreadsheet")
    sheet_id: int = Field(description="Numeric tab ID")
    start_row: int = Field(description="0-based start row index")
    end_row: int = Field(description="0-based end row index")
    start_col: int = Field(description="0-based start col index")
    end_col: int = Field(description="0-based end col index")
    cell_format: Dict[str, Any] = Field(description="A CellFormat payload containing cell formatting details")


class FormatRangeTool(BaseGoogleTool):
    name: str = "format_range"
    description: str = "Apply a visual format layout to a block of cells."
    args_schema: ArgsSchema = FormatRangeInput

    def _run(self, spreadsheet_id: str, sheet_id: int, start_row: int, end_row: int, start_col: int, end_col: int, cell_format: Dict[str, Any], config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError()

    async def _run_google_task(self, config: RunnableConfig, spreadsheet_id: str, sheet_id: int, start_row: int, end_row: int, start_col: int, end_col: int, cell_format: Dict[str, Any]) -> str:
        from google_client.services.sheets.types import CellFormat
        await adispatch_custom_event("tool_status", {"text": "Formatting Range...", "icon": "🎨"})
        sheets = await get_sheets_service(config)
        success = await sheets.format_range(spreadsheet_id, sheet_id, start_row, end_row, start_col, end_col, CellFormat(**cell_format))
        return "Success" if success else "Failed to format."


class MergeCellsInput(BaseModel):
    spreadsheet_id: str = Field(description="The ID of the spreadsheet")
    sheet_id: int = Field(description="Numeric tab ID")
    start_row: int = Field(description="0-based start row")
    end_row: int = Field(description="0-based end row")
    start_col: int = Field(description="0-based start col")
    end_col: int = Field(description="0-based end col")
    merge_type: str = Field(default="MERGE_ALL", description='Type of merge: MERGE_ALL, MERGE_COLUMNS, MERGE_ROWS')


class MergeCellsTool(BaseGoogleTool):
    name: str = "merge_cells"
    description: str = "Merge a grouping of cells into a single large cell."
    args_schema: ArgsSchema = MergeCellsInput

    def _run(self, spreadsheet_id: str, sheet_id: int, start_row: int, end_row: int, start_col: int, end_col: int, merge_type: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError()

    async def _run_google_task(self, config: RunnableConfig, spreadsheet_id: str, sheet_id: int, start_row: int, end_row: int, start_col: int, end_col: int, merge_type: str) -> str:
        await adispatch_custom_event("tool_status", {"text": "Merging Cells...", "icon": "🔗"})
        sheets = await get_sheets_service(config)
        success = await sheets.merge_cells(spreadsheet_id, sheet_id, start_row, end_row, start_col, end_col, merge_type)
        return "Success" if success else "Failed to merge."


class UnmergeCellsInput(BaseModel):
    spreadsheet_id: str = Field(description="The ID of the spreadsheet")
    sheet_id: int = Field(description="Numeric tab ID")
    start_row: int = Field(description="0-based start row")
    end_row: int = Field(description="0-based end row")
    start_col: int = Field(description="0-based start col")
    end_col: int = Field(description="0-based end col")


class UnmergeCellsTool(BaseGoogleTool):
    name: str = "unmerge_cells"
    description: str = "Unmerge previously merged cells."
    args_schema: ArgsSchema = UnmergeCellsInput

    def _run(self, spreadsheet_id: str, sheet_id: int, start_row: int, end_row: int, start_col: int, end_col: int, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError()

    async def _run_google_task(self, config: RunnableConfig, spreadsheet_id: str, sheet_id: int, start_row: int, end_row: int, start_col: int, end_col: int) -> str:
        await adispatch_custom_event("tool_status", {"text": "Unmerging Cells...", "icon": "⛓️"})
        sheets = await get_sheets_service(config)
        success = await sheets.unmerge_cells(spreadsheet_id, sheet_id, start_row, end_row, start_col, end_col)
        return "Success" if success else "Failed to unmerge."


class AutoResizeColumnsInput(BaseModel):
    spreadsheet_id: str = Field(description="The ID of the spreadsheet")
    sheet_id: int = Field(description="Numeric tab ID")
    start_col: int = Field(description="0-based start col")
    end_col: int = Field(description="0-based end col")


class AutoResizeColumnsTool(BaseGoogleTool):
    name: str = "auto_resize_columns"
    description: str = "Automatically resize columns to fit their content widths."
    args_schema: ArgsSchema = AutoResizeColumnsInput

    def _run(self, spreadsheet_id: str, sheet_id: int, start_col: int, end_col: int, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError()

    async def _run_google_task(self, config: RunnableConfig, spreadsheet_id: str, sheet_id: int, start_col: int, end_col: int) -> str:
        await adispatch_custom_event("tool_status", {"text": "Resizing Columns...", "icon": "⇔"})
        sheets = await get_sheets_service(config)
        success = await sheets.auto_resize_columns(spreadsheet_id, sheet_id, start_col, end_col)
        return "Success" if success else "Failed to resize."


class InsertRowsInput(BaseModel):
    spreadsheet_id: str = Field(description="The ID of the spreadsheet")
    sheet_id: int = Field(description="Numeric tab ID")
    start_index: int = Field(description="0-based row insertion index")
    num_rows: int = Field(description="Number of empty rows to insert")


class InsertRowsTool(BaseGoogleTool):
    name: str = "insert_rows"
    description: str = "Insert full empty rows pushing content down."
    args_schema: ArgsSchema = InsertRowsInput

    def _run(self, spreadsheet_id: str, sheet_id: int, start_index: int, num_rows: int, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError()

    async def _run_google_task(self, config: RunnableConfig, spreadsheet_id: str, sheet_id: int, start_index: int, num_rows: int) -> str:
        await adispatch_custom_event("tool_status", {"text": "Inserting Rows...", "icon": "⏬"})
        sheets = await get_sheets_service(config)
        success = await sheets.insert_rows(spreadsheet_id, sheet_id, start_index, num_rows)
        return "Success" if success else "Failed to insert."


class DeleteRowsInput(BaseModel):
    spreadsheet_id: str = Field(description="The ID of the spreadsheet")
    sheet_id: int = Field(description="Numeric tab ID")
    start_index: int = Field(description="0-based row deletion start")
    end_index: int = Field(description="0-based row deletion end (exclusive)")


class DeleteRowsTool(BaseGoogleTool):
    name: str = "delete_rows"
    description: str = "Delete entire rows."
    args_schema: ArgsSchema = DeleteRowsInput

    def _run(self, spreadsheet_id: str, sheet_id: int, start_index: int, end_index: int, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError()

    async def _run_google_task(self, config: RunnableConfig, spreadsheet_id: str, sheet_id: int, start_index: int, end_index: int) -> str:
        await adispatch_custom_event("tool_status", {"text": "Deleting Rows...", "icon": "⌫"})
        sheets = await get_sheets_service(config)
        success = await sheets.delete_rows(spreadsheet_id, sheet_id, start_index, end_index)
        return "Success" if success else "Failed to delete."


class SortRangeInput(BaseModel):
    spreadsheet_id: str = Field(description="The ID of the spreadsheet")
    sheet_id: int = Field(description="Numeric tab ID")
    start_row: int = Field(description="0-based start row")
    end_row: int = Field(description="0-based end row")
    start_col: int = Field(description="0-based start col")
    end_col: int = Field(description="0-based end col")
    sort_column_index: int = Field(description="Column index to sort by")
    ascending: bool = Field(default=True, description="Sort direction")


class SortRangeTool(BaseGoogleTool):
    name: str = "sort_range"
    description: str = "Dynamically sort a grid layout block by a target column index."
    args_schema: ArgsSchema = SortRangeInput

    def _run(self, spreadsheet_id: str, sheet_id: int, start_row: int, end_row: int, start_col: int, end_col: int, sort_column_index: int, ascending: bool, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError()

    async def _run_google_task(self, config: RunnableConfig, spreadsheet_id: str, sheet_id: int, start_row: int, end_row: int, start_col: int, end_col: int, sort_column_index: int, ascending: bool) -> str:
        await adispatch_custom_event("tool_status", {"text": "Sorting Range...", "icon": "🏷️"})
        sheets = await get_sheets_service(config)
        success = await sheets.sort_range(spreadsheet_id, sheet_id, start_row, end_row, start_col, end_col, sort_column_index, ascending)
        return "Success" if success else "Failed to sort."


class FreezeRowsInput(BaseModel):
    spreadsheet_id: str = Field(description="The ID of the spreadsheet")
    sheet_id: int = Field(description="Numeric tab ID")
    num_rows: int = Field(description="Number of rows to freeze at the top")


class FreezeRowsTool(BaseGoogleTool):
    name: str = "freeze_rows"
    description: str = "Freeze the top header block limit horizontally."
    args_schema: ArgsSchema = FreezeRowsInput

    def _run(self, spreadsheet_id: str, sheet_id: int, num_rows: int, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError()

    async def _run_google_task(self, config: RunnableConfig, spreadsheet_id: str, sheet_id: int, num_rows: int) -> str:
        await adispatch_custom_event("tool_status", {"text": "Freezing Rows...", "icon": "❄️"})
        sheets = await get_sheets_service(config)
        success = await sheets.freeze_rows(spreadsheet_id, sheet_id, num_rows)
        return "Success" if success else "Failed to freeze rows."


class AddDataValidationInput(BaseModel):
    spreadsheet_id: str = Field(description="The ID of the spreadsheet")
    sheet_id: int = Field(description="Numeric tab ID")
    start_row: int = Field(description="0-based start row")
    end_row: int = Field(description="0-based end row")
    start_col: int = Field(description="0-based start col")
    end_col: int = Field(description="0-based end col")
    dropdown_values: List[str] = Field(description="List of strings for dropdown enums")


class AddDataValidationTool(BaseGoogleTool):
    name: str = "add_data_validation"
    description: str = "Inject a dropdown checklist onto the grid bounds."
    args_schema: ArgsSchema = AddDataValidationInput

    def _run(self, spreadsheet_id: str, sheet_id: int, start_row: int, end_row: int, start_col: int, end_col: int, dropdown_values: List[str], config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError()

    async def _run_google_task(self, config: RunnableConfig, spreadsheet_id: str, sheet_id: int, start_row: int, end_row: int, start_col: int, end_col: int, dropdown_values: List[str]) -> str:
        await adispatch_custom_event("tool_status", {"text": "Adding Validation...", "icon": "✅"})
        sheets = await get_sheets_service(config)
        success = await sheets.add_data_validation(spreadsheet_id, sheet_id, start_row, end_row, start_col, end_col, dropdown_values)
        return "Success" if success else "Failed to add data validation."


class BatchUpdateInput(BaseModel):
    spreadsheet_id: str = Field(description="The ID of the spreadsheet")
    requests: List[Dict[str, Any]] = Field(description="A list of dict payloads for Google Sheets API")


class BatchUpdateTool(BaseGoogleTool):
    name: str = "batch_update"
    description: str = "Provide programmatic direct manipulation over complex cell changes."
    args_schema: ArgsSchema = BatchUpdateInput

    def _run(self, spreadsheet_id: str, requests: List[Dict[str, Any]], config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError()

    async def _run_google_task(self, config: RunnableConfig, spreadsheet_id: str, requests: List[Dict[str, Any]]) -> str:
        await adispatch_custom_event("tool_status", {"text": "Batch Updating...", "icon": "⚙️"})
        sheets = await get_sheets_service(config)
        try:
            result = await sheets.batch_update(spreadsheet_id, requests)
            return json.dumps(result)
        except Exception as e:
            return f"Failed: {str(e)}"

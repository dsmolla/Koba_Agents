from pathlib import Path

from langchain.agents.structured_output import ToolStrategy
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import PromptTemplate
from langgraph.checkpoint.base import BaseCheckpointSaver

from agents.common.agent import BaseAgent, agent_to_tool
from agents.gmail.agent import GmailAgent
from agents.google_calendar.agent import CalendarAgent
from agents.google_drive.agent import DriveAgent
from agents.google_tasks.agent import TasksAgent
from agents.google_docs.agent import DocsAgent
from agents.google_sheets.agent import SheetsAgent
from core.models import BotMessage
from .common.tools import CurrentDateTimeTool
from .memory import CreateMemoryTool, UpdateMemoryTool, DeleteMemoryTool

# Cache the raw prompt text at module level — read from disk once, not per instantiation
_SYSTEM_PROMPT_TEMPLATE = Path(__file__).parent.joinpath('system_prompt.txt').read_text()


class SupervisorAgent(BaseAgent):
    name: str = "SupervisorAgent"
    description: str = "A Google Workspace expert that can handle complex queries related to Gmail, Calendar, Tasks, and Drive"

    def __init__(self, model: BaseChatModel, checkpointer: BaseCheckpointSaver):
        tools = [
            agent_to_tool(agent) for agent in [
                GmailAgent(model),
                CalendarAgent(model),
                TasksAgent(model),
                DriveAgent(model),
                DocsAgent(model),
                SheetsAgent(model),
            ]
        ] + [CurrentDateTimeTool(), CreateMemoryTool(), UpdateMemoryTool(), DeleteMemoryTool()]

        tool_descriptions = "\n".join(f"- {tool.name}: {tool.description}" for tool in tools)
        system_prompt = PromptTemplate.from_template(_SYSTEM_PROMPT_TEMPLATE).format(
            tools=tool_descriptions
        )

        response_format = ToolStrategy(BotMessage)

        super().__init__(model, tools, system_prompt, checkpointer, response_format)

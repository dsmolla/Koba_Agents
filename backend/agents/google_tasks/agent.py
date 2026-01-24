from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import PromptTemplate

from agents.common.agent import BaseAgent
from agents.common.tools import CurrentDateTimeTool
from .tools import CreateTaskTool, ListTasksTool, DeleteTaskTool, CompleteTaskTool, ReopenTaskTool, UpdateTaskTool, \
    CreateTaskListTool, ListTaskListsTool


class TasksAgent(BaseAgent):
    name: str = "TasksAgent"
    description: str = "A Google Tasks expert that can handle complex tasks and queries related to Google Tasks management"

    def __init__(self, model: BaseChatModel):
        tools = [
            CurrentDateTimeTool(),
            CreateTaskTool(),
            ListTasksTool(),
            DeleteTaskTool(),
            CompleteTaskTool(),
            ReopenTaskTool(),
            UpdateTaskTool(),
            CreateTaskListTool(),
            ListTaskListsTool(),
        ]

        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")
        system_prompt = PromptTemplate.from_file(str(Path(__file__).parent / 'system_prompt.txt'))
        system_prompt = system_prompt.format(tools='\n'.join(tool_descriptions))

        super().__init__(model, tools, system_prompt)

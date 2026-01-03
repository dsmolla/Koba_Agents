from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import PromptTemplate

from agents.gmail.agent import GmailAgent
from agents.google_calendar.agent import CalendarAgent
from agents.google_drive.agent import DriveAgent
from agents.google_tasks.agent import TasksAgent
from agents.common.agent import BaseAgent, agent_to_tool
from .common.tools import CurrentDateTimeTool


class GoogleAgent(BaseAgent):
    name: str = "SupervisorAgent"
    description: str = "A Google Workspace expert that can handle complex queries related to Gmail, Calendar, Tasks, and Drive"

    def __init__(self, model: BaseChatModel):
        tools = [
            agent_to_tool(agent) for agent in [
                GmailAgent(model),
                CalendarAgent(model),
                TasksAgent(model),
                DriveAgent(model),
            ]
        ] + [CurrentDateTimeTool()]

        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")
        system_prompt = PromptTemplate.from_file(str(Path(__file__).parent / 'system_prompt.txt'))
        system_prompt = system_prompt.format(tools='\n'.join(tool_descriptions))

        super().__init__(model, tools, system_prompt)

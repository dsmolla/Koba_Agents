from langchain_core.messages import HumanMessage
from langchain_core.tools import BaseTool, ArgsSchema
from pydantic import BaseModel, Field

from agents.calendar.agent import CalendarAgent
from agents.drive.agent import DriveAgent
from agents.gmail.agent import GmailAgent
from agents.tasks.agent import TasksAgent


class AgentInput(BaseModel):
    task_description: str = Field(description="A detailed description of the task.")


class GmailTool(BaseTool):
    name: str = "gmail_agent_tool"
    description: str = "Handles any kind of Gmail operation"
    args_schema: ArgsSchema = AgentInput

    gmail_agent: GmailAgent

    def __init__(self, gmail_agent: GmailAgent):
        super().__init__(gmail_agent=gmail_agent)

    def _run(self, task_description: str) -> str:
        response = self.gmail_agent.execute([HumanMessage(task_description)])
        return response.messages[-1].content


class TasksTool(BaseTool):
    name: str = "tasks_agent_tool"
    description: str = "Handles any kind of operation related to Google Tasks"
    args_schema: ArgsSchema = AgentInput

    tasks_agent: TasksAgent

    def __init__(self, tasks_agent: TasksAgent):
        super().__init__(tasks_agent=tasks_agent)

    def _run(self, task_description: str) -> str:
        response = self.tasks_agent.execute([HumanMessage(task_description)])
        return response.messages[-1].content


class CalendarTool(BaseTool):
    name: str = "calendar_agent_tool"
    description: str = "Handles any kind of operation related to Google Calendar"
    args_schema: ArgsSchema = AgentInput

    calendar_agent: CalendarAgent

    def __init__(self, calendar_agent: CalendarAgent):
        super().__init__(calendar_agent=calendar_agent)

    def _run(self, task_description: str) -> str:
        response = self.calendar_agent.execute([HumanMessage(task_description)])
        return response.messages[-1].content


class DriveTool(BaseTool):
    name: str = "drive_agent_tool"
    description: str = "Handles any kind of operation related to Google Drive files and folders"
    args_schema: ArgsSchema = AgentInput

    drive_agent: DriveAgent

    def __init__(self, drive_agent: DriveAgent):
        super().__init__(drive_agent=drive_agent)

    def _run(self, task_description: str) -> str:
        response = self.drive_agent.execute([HumanMessage(task_description)])
        return response.messages[-1].content

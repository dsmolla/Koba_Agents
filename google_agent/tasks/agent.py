from google_client.api_service import APIServiceLayer
from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from .system_prompt import system_prompt
from .task_list_cache import TaskListCache
from .tools import CreateTaskTool, ListTasksTool, DeleteTaskTool, CompleteTaskTool, ReopenTaskTool, UpdateTaskTool, \
    CreateTaskListTool, ListTaskListsTool
from ..shared.tools import CurrentDateTimeTool


class TasksAgent:
    name: str = "TasksAgent"
    description: str = "A Google Tasks expert that can handle complex tasks and queries related to Google Tasks management"

    def __init__(
            self,
            google_service: APIServiceLayer,
            llm: BaseChatModel,
            config: RunnableConfig = None
    ):
        self._task_list_cache = TaskListCache()
        self._tools = [
            CurrentDateTimeTool(google_service.timezone),
            CreateTaskTool(google_service),
            ListTasksTool(google_service),
            DeleteTaskTool(google_service),
            CompleteTaskTool(google_service),
            ReopenTaskTool(google_service),
            UpdateTaskTool(google_service),
            CreateTaskListTool(google_service, self._task_list_cache),
            ListTaskListsTool(google_service, self._task_list_cache),
        ]

        self.agent = create_agent(
            name=self.name,
            model=llm,
            tools=self._tools,
            system_prompt=system_prompt.format(
                tools="\n".join([f"- {tool.name}: {tool.description}" for tool in self._tools])),
        )

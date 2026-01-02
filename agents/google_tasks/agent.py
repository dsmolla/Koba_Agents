from google_client.api_service import APIServiceLayer
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from agents.shared.base_agent import BaseReactGoogleAgent
from agents.shared.tools import CurrentDateTimeTool
from .task_list_cache import TaskListCache
from .tools import CreateTaskTool, ListTasksTool, DeleteTaskTool, CompleteTaskTool, ReopenTaskTool, UpdateTaskTool, \
    CreateTaskListTool, ListTaskListsTool


class TasksAgent(BaseReactGoogleAgent):
    name: str = "TasksAgent"
    description: str = "A Google Tasks expert that can handle complex tasks and queries related to Google Tasks management"

    def __init__(
            self,
            google_service: APIServiceLayer,
            llm: BaseChatModel,
            config: RunnableConfig = None
    ):
        self.task_list_cache = TaskListCache()
        super().__init__(google_service, llm, config)

    @property
    def tools(self):
        if self._tools is None:
            self._tools = [
                CurrentDateTimeTool(self.google_service.timezone),
                CreateTaskTool(self.google_service),
                ListTasksTool(self.google_service),
                DeleteTaskTool(self.google_service),
                CompleteTaskTool(self.google_service),
                ReopenTaskTool(self.google_service),
                UpdateTaskTool(self.google_service),
                CreateTaskListTool(self.google_service, self.task_list_cache),
                ListTaskListsTool(self.google_service, self.task_list_cache),
            ]
        return self._tools

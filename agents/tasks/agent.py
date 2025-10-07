from datetime import datetime
from textwrap import dedent
from typing import List, Dict

from google_client.services.tasks import TasksApiService
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from shared.base_agent import BaseAgent
from .task_list_cache import TaskListCache
from .tools import CreateTaskTool, ListTasksTool, DeleteTaskTool, CompleteTaskTool, ReopenTaskTool, UpdateTaskTool, \
    CreateTaskListTool, ListTaskListsTool


class TasksAgent(BaseAgent):
    name: str = "TasksAgent"
    description: str = "A Google Tasks expert that can handle complex tasks and queries related to Google Tasks management"

    def __init__(
            self,
            tasks_service: TasksApiService,
            llm: BaseChatModel,
            config: RunnableConfig = None,
            print_steps: bool = False,
    ):
        self.tasks_service = tasks_service
        self.task_list_cache = TaskListCache()
        super().__init__(llm, config, print_steps)

    def _get_tools(self):
        return [
            CreateTaskTool(self.tasks_service),
            ListTasksTool(self.tasks_service),
            DeleteTaskTool(self.tasks_service),
            CompleteTaskTool(self.tasks_service),
            ReopenTaskTool(self.tasks_service),
            UpdateTaskTool(self.tasks_service),
            CreateTaskListTool(self.tasks_service, self.task_list_cache),
            ListTaskListsTool(self.tasks_service, self.task_list_cache),
        ]

    def system_prompt(self):
        tool_descriptions = []
        for tool in self.tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")

        return dedent(
            f"""
            # Identity

            You are a Google Tasks assistant that can handle complex tasks and queries related to task management. You have access to the following tools:
            {'\n'.join(tool_descriptions)}

            # Instructions

            * Always start by drafting a plan
            * Break down requests into smaller requests for each tool.
            * Identify the tools you need and in what order.
            * Always wait for the output of the tools before making another tool call
            * At the end, summarize what actions were taken and give the user a detailed answer to their query.
            * Always include task_ids and task_list_ids in your response.
            * Every question the user asks you is related to Google Tasks. If they ask you for any information that seems unrelated to tasks, try to find that information in their task lists.

            CURRENT DATE AND TIME: {datetime.now().strftime("%Y-%m-%d %H:%M")}

            # Example

            User: create a task called "Buy groceries" due tomorrow
            AI: tool_call('create_task', args={{'title': 'Buy groceries', 'due': '2024-01-02'}})
            Respond: Respond to user
            -----

            User: show me all my tasks
            AI: tool_call('list_task_lists', args={{}})
            Check: Check output from tool_call and find task_list_ids
            AI: tool_call('list_tasks', args={{<task_list_id[0]_from_previous_call>}})
            AI: tool_call('list_tasks', args={{<task_list_id[1]_from_previous_call>}})
            .
            .
            .
            AI: tool_call('list_tasks', args={{<task_list_id[n]_from_previous_call>}})
            Respond: Respond to user
            -----

            User: mark "Buy groceries" from the "household" list as complete
            AI: tool_call('list_task_lists', args={{}})
            Check: Check output from tool_call and find task_list_id of "household"
            AI: tool_call('list_tasks', args={{'task_list_id': <task_list_id_from_previous_call>}})
            Check: Check output from tool_call and find task_id for "Buy groceries"
            AI: tool_call('complete_task', args={{'task_id': '<task_id_from_previous_call>', 'task_list_id': <task_list_id_from_previous_call>}})
            Respond: Respond to user
            -----

            User: delete the task called "Old task"
            AI: tool_call('list_tasks', args={{}})
            Check: Check output from tool_call and find task_id for "Old task"
            AI: tool_call('delete_task', args={{'task_id': '<task_id_from_previous_call>'}})
            Respond: Respond to user
            -----

            User: create a new task list called "Work Tasks"
            AI: tool_call('create_task_list', args={{'title': 'Work Tasks'}})
            Respond: Respond to user
            -----

            * Replace <task_id_from_previous_call> with actual task_id from the previous tool call
            * Always include task_ids and task_list_ids in your response.

            """
        )


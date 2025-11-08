from datetime import datetime
from textwrap import dedent

from google_client.api_service import APIServiceLayer
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from google_agent.shared.base_agent import BaseAgent
from .task_list_cache import TaskListCache
from .tools import CreateTaskTool, ListTasksTool, DeleteTaskTool, CompleteTaskTool, ReopenTaskTool, UpdateTaskTool, \
    CreateTaskListTool, ListTaskListsTool


class TasksAgent(BaseAgent):
    name: str = "TasksAgent"
    description: str = "A Google Tasks expert that can handle complex tasks and queries related to Google Tasks management"

    def __init__(
            self,
            google_service: APIServiceLayer,
            llm: BaseChatModel,
            config: RunnableConfig = None,
            print_steps: bool = False,
    ):
        self.google_service = google_service
        self.task_list_cache = TaskListCache()
        super().__init__(llm, config, print_steps)

    def _get_tools(self):
        return [
            CreateTaskTool(self.google_service),
            ListTasksTool(self.google_service),
            DeleteTaskTool(self.google_service),
            CompleteTaskTool(self.google_service),
            ReopenTaskTool(self.google_service),
            UpdateTaskTool(self.google_service),
            CreateTaskListTool(self.google_service, self.task_list_cache),
            ListTaskListsTool(self.google_service, self.task_list_cache),
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

            ## Core Workflow
            * Always start by drafting a plan for multi-step operations
            * Break down complex requests into smaller, specific tool calls
            * Identify which tools you need and determine the correct execution order
            * Chain outputs: Use results from previous tool calls as inputs to subsequent calls
            * At the end, summarize all actions taken and provide a detailed answer to the user's query

            ## Response Guidelines
            * Always include Task ids and TaskList ids in your responses
            * Always provide clear, organized results

            ## Context Awareness
            * Current date and time: {datetime.now().strftime("%Y-%m-%d %H:%M")}

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

from datetime import datetime
from textwrap import dedent

from google_client.api_service import APIServiceLayer
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from google_agent.shared.base_agent import BaseAgent
from google_agent.shared.llm_models import LLM_LITE, LLM_FLASH
from .organization.agent import OrganizationAgent
from .search_and_retrieval.agent import SearchAndRetrievalAgent
from .tools import OrganizationTool, SearchAndRetrievalTool, WriterTool
from .writer.agent import WriterAgent
from ..shared.tools import CurrentDateTimeTool


class DriveAgent(BaseAgent):
    name: str = "DriveAgent"
    description: str = "A Google Drive expert that can handle complex tasks and queries related to Google Drive file management"

    def __init__(
            self,
            google_service: APIServiceLayer,
            llm: BaseChatModel,
            config: RunnableConfig = None,
    ):
        self.google_service = google_service
        super().__init__(llm, config)

    def _get_tools(self):
        organization_agent = OrganizationAgent(self.google_service, LLM_FLASH, self.config)
        search_and_retrieval_agent = SearchAndRetrievalAgent(self.google_service, LLM_LITE, self.config)
        writer_agent = WriterAgent(self.google_service, LLM_FLASH, self.config)

        return [
            CurrentDateTimeTool(self.google_service.timezone),
            OrganizationTool(organization_agent),
            SearchAndRetrievalTool(search_and_retrieval_agent),
            WriterTool(writer_agent),
        ]

    def system_prompt(self):
        tool_descriptions = []
        for tool in self.tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")

        return dedent(
            f"""
            # Identity

            You are a team supervisor for a Google Drive team. You have access to following experts or tools:
            {'\n'.join(tool_descriptions)}

            # Instructions

            ## Core Workflow
            * Always start by drafting a plan for multi-step operations
            * Break down complex requests into smaller, specific tool calls
            * Identify which tools you need and determine the correct execution order
            * Always wait for the output of one tool before making the next tool call
            * Chain outputs: Use results from previous tool calls as inputs to subsequent calls
            * Every question the user asks you is related to Google Drive files. If they ask you for any information that seems unrelated to files, try to find that information in their Drive.
            * At the end, summarize all actions taken and provide a detailed answer to the user's query

            ## Response Guidelines
            * Always include file IDs in your responses
            * Always include FULL FILE PATHS in your response for downloaded files
            * Always provide clear, organized results

            ## Context Awareness
            * Use the current_datetime_tool to get the current date and time when needed
            
            # Example

            User: create a folder called "Project Files" and upload my document to it
            AI: tool_call('writer_agent_tool', args={{'task_description': 'create a folder called "Project Files"'}})
            Check: Check output from tool_call and get folder_id
            AI: tool_call('writer_agent_tool', args={{'task_description': 'upload document to folder with id <folder_id>'}})
            Respond: Respond to user
            -----

            User: find all my spreadsheets from last month and organize them into a folder
            AI: tool_call('search_and_retrieval_agent_tool', args={{'task_description': 'find all my spreadsheets from last month'}}
            Check: Check output from tool_call and pass it to the next tool_call
            AI: tool_call('writer_agent_tool', args={{'task_description': 'create a folder for organizing spreadsheets'}})
            Check: Check output from tool_call and get folder_id
            AI: tool_call('organization_agent_tool', args={{'task_description': 'move the following spreadsheets to folder <folder_id>: <output from search_and_retrieval_agent_tool>'}})
            Respond: Respond to user
            -----

            User: rename all files in my "Old Project" folder to have "Archive" prefix
            AI: tool_call('search_and_retrieval_agent_tool', args={{'task_description': 'find all files in "Old Project" folder'}}
            Check: Check output from tool_call and pass it to the next tool_call
            AI: tool_call('organization_agent_tool', args={{'task_description': 'rename the following files to add "Archive" prefix: <output from search_and_retrieval_agent_tool>'}})
            Respond: Respond to user
            -----

            * Replace <output from ...agent_tool> with actual response from the agent

            """
        )

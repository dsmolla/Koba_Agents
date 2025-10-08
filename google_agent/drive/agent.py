from datetime import datetime
from textwrap import dedent

from google_client.services.drive import DriveApiService
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from google_agent.drive.shared.base_agent import BaseDriveAgent
from google_agent.shared.llm_models import LLM_LITE, LLM_FLASH, LLM_PRO
from .organization.agent import OrganizationAgent
from .search_and_retrieval.agent import SearchAndRetrievalAgent
from .tools import OrganizationTool, SearchAndRetrievalTool, WriterTool
from .writer.agent import WriterAgent


class DriveAgent(BaseDriveAgent):
    name: str = "DriveAgent"
    description: str = "A Google Drive expert that can handle complex tasks and queries related to Google Drive file management"

    def __init__(
            self,
            drive_service: DriveApiService,
            llm: BaseChatModel,
            config: RunnableConfig = None,
            print_steps: bool = False,
    ):
        super().__init__(drive_service, llm, config, print_steps)

    def _get_tools(self):
        organization_agent = OrganizationAgent(self.drive_service, LLM_FLASH, self.config, self.print_steps)
        search_and_retrieval_agent = SearchAndRetrievalAgent(self.drive_service, LLM_LITE, self.config,
                                                             self.print_steps)
        writer_agent = WriterAgent(self.drive_service, LLM_PRO, self.config, self.print_steps)

        return [
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

            * You're task is to delegate tasks to these experts.
            * Always start by drafting a plan
            * Break down requests into smaller requests for each agent/tool.
            * Identify the tools/experts you need and in what order.
            * Always wait for the output of the tools/experts before making another tool call
            * At the end, summarize what actions were taken and and give the user a detailed answer to their query.
            * Always include file ids in your response since they are useful for follow-up actions.
            * Always include the exact full file paths for downloaded files. 
            * Every question the user asks you is related to Google Drive files. If they ask you for any information that seems unrelated to files, try to find that information in their Drive.

            CURRENT DATE AND TIME: {datetime.now().strftime("%Y-%m-%d %H:%M")}

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
            * Always include file ids in your response when they might be useful for follow-up actions.

            """
        )

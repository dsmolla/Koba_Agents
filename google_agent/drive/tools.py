from textwrap import dedent

from langchain_core.messages import HumanMessage
from langchain_core.tools import BaseTool, ArgsSchema
from pydantic import BaseModel, Field

from google_agent.drive.organization.agent import OrganizationAgent
from google_agent.drive.search_and_retrieval.agent import SearchAndRetrievalAgent
from google_agent.drive.writer.agent import WriterAgent


class AgentInput(BaseModel):
    task_description: str = Field(description="A detailed description of the task.")


class OrganizationTool(BaseTool):
    name: str = "organization_agent_tool"
    description: str = dedent(
        f"""
        Handles the following google drive operations:
            - move file or folder to different location
            - rename file or folder
            - delete file or folder
        """
    )
    args_schema: ArgsSchema = AgentInput

    organization_agent: OrganizationAgent

    def __init__(self, organization_agent: OrganizationAgent):
        super().__init__(organization_agent=organization_agent)

    def _run(self, task_description: str) -> str:
        response = self.organization_agent.execute([HumanMessage(task_description)])
        return response.messages[-1].content


class SearchAndRetrievalTool(BaseTool):
    name: str = "search_and_retrieval_agent_tool"
    description: str = dedent(
        f"""
        Handles the following google drive operations:
            - search for files and folders
            - get detailed file information
            - download file content
            - list folder contents
            - get file permissions
        """
    )
    args_schema: ArgsSchema = AgentInput

    search_and_retrieval_agent: SearchAndRetrievalAgent

    def __init__(self, search_and_retrieval_agent: SearchAndRetrievalAgent):
        super().__init__(search_and_retrieval_agent=search_and_retrieval_agent)

    def _run(self, task_description: str) -> str:
        response = self.search_and_retrieval_agent.execute([HumanMessage(task_description)])
        return response.messages[-1].content


class WriterTool(BaseTool):
    name: str = "writer_agent_tool"
    description: str = dedent(
        f"""
        Handles the following google drive operations:
            - upload file to Drive
            - create new folder
            - share file or folder with others
        """
    )
    args_schema: ArgsSchema = AgentInput

    writer_agent: WriterAgent

    def __init__(self, writer_agent: WriterAgent):
        super().__init__(writer_agent=writer_agent)

    def _run(self, task_description: str) -> str:
        response = self.writer_agent.execute([HumanMessage(task_description)])
        return response.messages[-1].content

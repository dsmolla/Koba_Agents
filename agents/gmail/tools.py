from textwrap import dedent

from langchain_core.messages import HumanMessage
from langchain_core.tools import BaseTool, ArgsSchema
from pydantic import BaseModel, Field

from agents.gmail.organization.agent import OrganizationAgent
from agents.gmail.search_and_retrieval.agent import SearchAndRetrievalAgent
from agents.gmail.summary_and_analytics.agent import SummaryAndAnalyticsAgent
from agents.gmail.writer.agent import WriterAgent


class AgentInput(BaseModel):
    task_description: str = Field(description="A detailed description of the task.")


class OrganizationTool(BaseTool):
    name: str = "organization_agent_tool"
    description: str = dedent(
        f"""
        Handles the following gmail operations:
            - apply label to email
            - remove label from email
            - create a new label
            - delete a label
            - rename a label
            - delete an email
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
        Handles the following gmail operations:
            - get full email
            - search for emails
            - list user created labels
            - download email attachments
        """
    )
    args_schema: ArgsSchema = AgentInput

    search_and_retrieval_agent: SearchAndRetrievalAgent

    def __init__(self, search_and_retrieval_agent: SearchAndRetrievalAgent):
        super().__init__(search_and_retrieval_agent=search_and_retrieval_agent)

    def _run(self, task_description: str) -> str:
        response = self.search_and_retrieval_agent.execute([HumanMessage(task_description)])
        return response.messages[-1].content


class SummaryAndAnalyticsTool(BaseTool):
    name: str = "summary_and_analytics_agent_tool"
    description: str = dedent(
        f"""
        Handles the following gmail operations:
            - summarize an email or a list of emails
            - extract data from email
            - classify emails into categories
        """
    )
    args_schema: ArgsSchema = AgentInput

    summary_and_analytics_agent: SummaryAndAnalyticsAgent

    def __init__(self, summary_and_analytics_agent: SummaryAndAnalyticsAgent):
        super().__init__(summary_and_analytics_agent=summary_and_analytics_agent)

    def _run(self, task_description: str) -> str:
        response = self.summary_and_analytics_agent.execute([HumanMessage(task_description)])
        return response.messages[-1].content


class WriterTool(BaseTool):
    name: str = "writer_agent_tool"
    description: str = dedent(
        f"""
        Handles the following gmail operations:
            - send an email
            - create a draft
            - reply to an email
            - forward an email
        """
    )
    args_schema: ArgsSchema = AgentInput

    writer_agent: WriterAgent

    def __init__(self, writer_agent: WriterAgent):
        super().__init__(writer_agent=writer_agent)

    def _run(self, task_description: str) -> str:
        response = self.writer_agent.execute([HumanMessage(task_description)])
        return response.messages[-1].content

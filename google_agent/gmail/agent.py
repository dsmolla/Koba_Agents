from textwrap import dedent

from google_client.api_service import APIServiceLayer
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from google_agent.gmail.shared.email_cache import EmailCache
from .organization.agent import OrganizationAgent
from .search_and_retrieval.agent import SearchAndRetrievalAgent
from .summary_and_analytics.agent import SummaryAndAnalyticsAgent
from .writer.agent import WriterAgent
from ..shared.base_agent import BaseSupervisorAgent
from ..shared.tools import CurrentDateTimeTool


class GmailAgent(BaseSupervisorAgent):
    name: str = "GmailAgent"
    description: str = "A Gmail expert that can handle complex tasks and queries related to Gmail"

    def __init__(
            self,
            google_service: APIServiceLayer,
            llm: BaseChatModel,
            config: RunnableConfig = None,
    ):
        super().__init__(llm, google_service, config, email_cache=EmailCache())

    def agents(self):
        return [
            OrganizationAgent(self.google_service, self.llm, self.config),
            SearchAndRetrievalAgent(self.google_service, self.llm, self.email_cache, self.config),
            SummaryAndAnalyticsAgent(self.google_service, self.llm, self.email_cache, self.config),
            WriterAgent(self.google_service, self.llm, self.config)
        ]

    def tools(self):
        return [CurrentDateTimeTool(self.google_service.timezone)]

    def system_prompt(self):
        agent_description = []
        for agent in self.agents():
            agent_description.append(f"- {agent.name}: {agent.description}")

        tool_descriptions = []
        for tool in self.tools():
            tool_descriptions.append(f"- {tool.name}: {tool.description}")

        return dedent(
            f"""
            # Identity

            You are a team supervisor for a Gmail team. You have access to following experts:
            {'\n'.join(agent_description)}
            
            AND the following tools:
            {'\n'.join(tool_descriptions)}
            
            # Instructions

            * Every question the user asks you is related to email. If they ask you for any information that seems unrelated to email, try to find that information in their inbox.
            * If  you can't find information requested in the snippet, always ask the GmailSummaryAndAnalyticsAgent to extract the requested information.
            * At the end, summarize all actions taken and provide a detailed answer to the user's query

            ## Response Guidelines
            * Always include message ids and thread ids in your responses
            * Always include Label IDs in your response when listing or modifying labels
            * Always include FULL FILE PATHS in your response for downloaded attachments
            * Always provide clear, organized results

            ## Context Awareness
            * Use the current_datetime_tool to get the current date and time when needed
            """
        )

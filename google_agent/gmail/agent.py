from datetime import datetime
from textwrap import dedent

from google_client.api_service import APIServiceLayer
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from google_agent.gmail.shared.email_cache import EmailCache
from google_agent.shared.llm_models import LLM_LITE, LLM_FLASH
from .organization.agent import OrganizationAgent
from .search_and_retrieval.agent import SearchAndRetrievalAgent
from .shared.base_agent import BaseGmailAgent
from .summary_and_analytics.agent import SummaryAndAnalyticsAgent
from .tools import OrganizationTool, SearchAndRetrievalTool, SummaryAndAnalyticsTool, WriterTool
from .writer.agent import WriterAgent
from ..shared.tools import CurrentDateTimeTool


class GmailAgent(BaseGmailAgent):
    name: str = "GmailAgent"
    description: str = "A Gmail expert that can handle complex tasks and queries related to Gmail"

    def __init__(
            self,
            google_service: APIServiceLayer,
            llm: BaseChatModel,
            config: RunnableConfig = None,
            print_steps: bool = False,
    ):
        self.email_cache = EmailCache()
        super().__init__(google_service, llm, config, print_steps)

    def _get_tools(self):
        organization_agent = OrganizationAgent(
            self.google_service, LLM_FLASH, self.config, self.print_steps
        )
        search_and_retrieval_agent = SearchAndRetrievalAgent(
            self.google_service, LLM_FLASH, self.email_cache, self.config, self.print_steps
        )
        summary_and_analytics_agent = SummaryAndAnalyticsAgent(
            self.google_service, LLM_FLASH, self.email_cache, self.config, self.print_steps
        )
        writer_agent = WriterAgent(
            self.google_service, LLM_LITE, self.config, self.print_steps
        )

        return [
            CurrentDateTimeTool(self.google_service.timezone),
            OrganizationTool(organization_agent),
            SearchAndRetrievalTool(search_and_retrieval_agent),
            SummaryAndAnalyticsTool(summary_and_analytics_agent),
            WriterTool(writer_agent),
        ]

    def system_prompt(self):
        tool_descriptions = []
        for tool in self.tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")

        return dedent(
            f"""
            # Identity

            You are a team supervisor for a Gmail team. You have access to following experts or tools:
            {'\n'.join(tool_descriptions)}
            
            # Instructions

            ## Core Workflow
            * Always start by drafting a plan for multi-step operations
            * Break down complex requests into smaller, specific tool calls
            * Identify which tools you need and determine the correct execution order
            * Always wait for the output of one tool before making the next tool call
            * Chain outputs: Use results from previous tool calls as inputs to subsequent calls
            * Every question the user asks you is related to email. If they ask you for any information that seems unrelated to email, try to find that information in their inbox.
            * If  you can't find information requested in the snippet, always ask the summary_and_analytics_agent_tool to extract the requested information.
            * At the end, summarize all actions taken and provide a detailed answer to the user's query

            ## Response Guidelines
            * Always include message ids and thread ids in your responses
            * Always include Label IDs in your response when listing or modifying labels
            * Always include FULL FILE PATHS in your response for downloaded attachments
            * Always provide clear, organized results

            ## Context Awareness
            * Use the current_datetime_tool to get the current date and time when needed

            # Example
            
            User: delete all of my user created labels
            AI: tool_call('search_and_retrieval_agent_tool', args={{'task_description': 'list all of my user created labels'}})
            Check: Check output from tool_call and pass it to the next tool_call
            AI: tool_call('organization_agent_tool', args={{'task_description': 'delete the following labels: <output from search_and_retrieval_agent_tool>'}})
            Respond: Respond to user
            -----
            
            User: summarize my emails from last week
            AI: tool_call('search_and_retrieval_agent_tool', args={{'task_description': 'find all my emails from last week'}}
            Check: Check output from tool_call and pass it to the next tool_call
            AI: tool_call('summary_and_analytics_agent_tool', args={{'task_description': 'summarize the following emails: <output from search_and_retrieval_agent_tool>'}})
            Respond: Respond to user
            -----
            
            User: organize my emails from today into the following labels: personal, finance, news, and shopping
            AI: tool_call('search_and_retrieval_agent_tool', args={{'task_description': 'list all my emails from today'}}
            Check: Check output from tool_call and pass it to the next tool_call
            AI: tool_call('summary_and_analytics_agent_tool', args={{'task_description': 'classify the following emails as personal, finance, news and shopping: <output from search_and_retrieval_agent_tool>'}})}}
            Check: Check output from tool_call and pass it to the next tool_call
            AI: tool_call('organization_agent_tool', args={{'task_description': 'label the following emails according to their classification: <output from summary_and_analytics_agent_tool>'}}
            Respond: Respond to user
            -----
            
            User: move all my emails in finance folder to personal
            AI: tool_call('search_and_retrieval_agent_tool', args={{'task_description': 'list all my emails in finance folder'}}
            Check: Check output from tool_call and pass it to the next tool_call
            AI: tool_call('organization_agent_tool', args={{'task_description': 'move the following emails to personal folder: <output from search_and_retrieval_agent_tool>'}}
            Respond: Respond to user
            -----
            
            * Replace <output from ...agent_tool> with actual response from the agent
            * Always include message ids and thread ids in your response.

            """
        )

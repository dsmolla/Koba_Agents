from datetime import datetime
from textwrap import dedent
from typing import List, Dict

from google_client.services.gmail import GmailApiService
from langchain_core.language_models import BaseChatModel
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI

from agents.gmail.shared.email_cache import EmailCache
from shared.llm_models import MODELS
from .organization.agent import OrganizationAgent
from .search_and_retrieval.agent import SearchAndRetrievalAgent
from .shared.base_agent import BaseGmailAgent
from .summary_and_analytics.agent import SummaryAndAnalyticsAgent
from .tools import OrganizationTool, SearchAndRetrievalTool, SummaryAndAnalyticsTool, WriterTool
from .writer.agent import WriterAgent

RATE_LIMITER = InMemoryRateLimiter(
    requests_per_second=0.16,  # 10 RPM
    check_every_n_seconds=0.1,
    max_bucket_size=10
)

LLM_FLASH = ChatGoogleGenerativeAI(
    model=MODELS['gemini']['flash'],
    rate_limiter=RATE_LIMITER,
)

LLM_PRO = ChatGoogleGenerativeAI(
    model=MODELS['gemini']['pro'],
    rate_limiter=RATE_LIMITER,
)

LLM_LITE = ChatGoogleGenerativeAI(
    model=MODELS['gemini']['flash_lite'],
    rate_limiter=RATE_LIMITER,
)


class GmailAgent(BaseGmailAgent):
    name: str = "GmailAgent"
    description: str = "A Gmail expert that can handle complex tasks and queries related to Gmail"

    def __init__(
            self,
            gmail_service: GmailApiService,
            llm: BaseChatModel,
            config: RunnableConfig = None,
            print_steps: bool = False,
    ):
        self.email_cache = EmailCache()
        super().__init__(gmail_service, llm, config, print_steps)

    def _get_tools(self):
        organization_agent = OrganizationAgent(self.gmail_service, LLM_LITE, self.config, self.print_steps)
        search_and_retrieval_agent = SearchAndRetrievalAgent(self.gmail_service, LLM_FLASH, self.email_cache,
                                                             self.config, self.print_steps)
        summary_and_analytics_agent = SummaryAndAnalyticsAgent(self.gmail_service, LLM_PRO, self.email_cache,
                                                               self.config, self.print_steps)
        writer_agent = WriterAgent(self.gmail_service, LLM_FLASH, self.config, self.print_steps)

        return [
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
            
            * You're task is to delegate tasks to these experts.
            * Always start by drafting a plan 
            * Break down requests into smaller requests for each agent/tool.
            * Identify the tools/experts you need and in what order.
            * Always wait for the output of the tools/experts before making another tool call
            * At the end, summarize what actions were taken and and give the user a detailed answer to their query. 
            * Never include message ids and thread ids in your response.
            * Every question the user asks you is related to email. If they ask you for any information that seems unrelated to email, try to find that information in their inbox.
            * If a user asks for information about an email and you can't find it in the snippet, always ask the summary_and_analytics_agent_tool to extract the requested information.
            
            CURRENT DATE AND TIME: {datetime.now().strftime("%Y-%m-%d %H:%M")}

            # Example
            
            User: delete all of my user created labels
            AI: tool_call('organization_agent_tool', args={{'task_description': 'delete all of my user created labels'}})
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
            
            **Replace <output from ...agent_tool> with actual response from the agent
            """
        )

    def get_available_tools(self) -> List[Dict[str, str]]:
        return [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in self.tools
        ]

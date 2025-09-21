import json
from typing import Dict, List, Any, Optional, Callable
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage, BaseMessage
from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from google_client.services.gmail.api_service import GmailApiService
from textwrap import dedent
from dotenv import load_dotenv
import uuid

from .tools import (
    SearchThreadsTool,
    GetThreadDetailsTool,
    SummarizeThreadTool
)
from shared.constants import MODELS
from shared.exceptions import AgentException


load_dotenv()

LLM = ChatGoogleGenerativeAI(model=MODELS['gemini']['flash'])
# LLM = ChatAnthropic(model=MODELS['anthropic']['sonnet'])


class ThreadAgent:
    """Single ReAct Gmail Thread Agent for planning and execution"""
    name = "ThreadAgent"
    description = "Agent that can handle complex thread operations using Gmail tools"

    def __init__(
            self,
            gmail_service: GmailApiService,
            llm: BaseChatModel=LLM,
            memory: Optional[Any]=InMemorySaver(),
            config: Optional[Dict[str, Any]]= None,
            debug=False,
    ):
        self.gmail_service = gmail_service
        self.llm = llm
        self.memory = memory
        self.config = config
        self.debug = debug

        self.tools = self._get_tools()
        self.system_prompt = self._create_system_prompt()

        self.agent = create_react_agent(
            llm,
            self.tools,
            name="ThreadAgent",
            prompt=SystemMessage(self.system_prompt)
        )

    def _get_tools(self):
        """Initialize and return Gmail thread tools"""
        return [
            SearchThreadsTool(self.gmail_service),
            GetThreadDetailsTool(self.gmail_service),
            SummarizeThreadTool(self.gmail_service),
        ]

    def _create_system_prompt(self) -> str:
        """Create system prompt that encourages planning and execution"""
        tool_descriptions = []
        for tool in self.tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")

        return dedent(
            f"""You are a Gmail thread assistant that helps users manage and analyze email threads. You have access to the following Gmail thread tools:

            {', '.join(tool_descriptions)}

            When handling user requests:

            1. **THINK STEP BY STEP**: Break down complex requests into individual thread operations
            2. **PLAN YOUR APPROACH**: Identify what tools you need and in what order
            3. **EXECUTE SYSTEMATICALLY**: Use tools one by one, checking results before proceeding
            4. **HANDLE DEPENDENCIES**: When one operation depends on another (like summarizing a thread after finding it), use the output from the first operation
            5. **BE THOROUGH**: Make sure to complete all parts of the user's request
            6. **PROVIDE CLEAR UPDATES**: Explain what you're doing and the results
            7. **THREAD ANALYSIS**: When analyzing threads, consider the conversation flow, participants, and key topics
            8. **THREAD SEARCH**: When searching for threads, if you can't find any matching the criteria, try with relaxed criteria or different search terms
            9. **FINAL SUMMARY**: At the end, summarize what actions were taken and their outcomes.
                                    Always include the thread ID's and message ID's of emails along with whatever information or action is requested as the user might need it for another operation.
                                 

            For multi-step operations:
            - Search for threads first using appropriate filters
            - Get detailed thread information when needed for analysis
            - Summarize threads based on user requirements (conversation, key_points, or action_items)
            - Handle errors gracefully and inform the user

            **Thread Summary Types Available:**
            - **conversation**: General overview of the thread discussion
            - **key_points**: Extract main points and decisions from the thread
            - **action_items**: Extract tasks, follow-ups, and action items

            **SEARCH CAPABILITIES**: You can search threads by sender, recipient, subject, date ranges, labels, and various filters.

            Always aim to fully complete the user's request using the available Gmail thread tools.
        """)

    def get_available_tools(self) -> List[Dict[str, str]]:
        """Get information about available tools"""
        return [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in self.tools
        ]

    def execute(self, user_input: BaseMessage) -> Dict[str, Any]:
        """Execute the user request using ReAct agent"""
        try:
            tool_outputs = []
            agent_responses = []

            for chunk in self.agent.stream({"messages": [user_input]}, stream_mode="values", config=self.config):
                response = chunk['messages'][-1]

                if isinstance(response, AIMessage):
                    if response.content:
                        agent_responses.append(response.content)
                        if self.debug:
                            print(f"Agent Output - {response.name}: {response.content}")
                    if self.debug and response.tool_calls:
                        print(f"Tool calls - {response.name}:")
                        for tool_call in response.tool_calls:
                            print(tool_call)

                elif isinstance(response, ToolMessage):
                    tool_outputs.append({
                        "tool_name": response.name,
                        "content": response.content
                    })
                    if self.debug:
                        print(f"Tool output - {response.name}: {response.content}")

                if self.debug:
                    print("-----\n")

            return {
                "success": self._check_success(tool_outputs),
                "tool_outputs": tool_outputs,
                "final_response": agent_responses[-1],
            }

        except Exception as e:
            raise AgentException(message=f"Agent execution failed: {str(e)}", agent_name=self.name)

    def create_agent(self):
        """Create and return the LangGraph agent for use in supervisor pattern"""
        return self.agent

    @staticmethod
    def _check_success(tool_outputs: List[Dict[str, Any]]) -> bool:
        """Check if the agent execution was successful based on tool outputs"""
        return len(tool_outputs) > 0 and not tool_outputs[-1]["content"].startswith("Error: ")
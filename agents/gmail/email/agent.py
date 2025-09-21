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

from .tools import (
    GetEmailTool,
    SearchEmailsTool,
    SendEmailTool,
    DraftEmailTool,
    ReplyEmailTool,
    ForwardEmailTool,
    DeleteEmailTool,
    DownloadAttachmentTool
)
from shared.constants import MODELS
from shared.exceptions import AgentException


load_dotenv()

LLM = ChatGoogleGenerativeAI(model=MODELS['gemini']['flash'])
# LLM = ChatAnthropic(model=MODELS['anthropic']['sonnet'])


class EmailAgent:
    """Single ReAct Gmail Agent for planning and execution"""
    name = "EmailAgent"
    description = "Agent that can handle complex email operations using Gmail tools"

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
            name="EmailAgent",
            prompt=SystemMessage(self.system_prompt)
        )


    def _get_tools(self):
        """Initialize and return Gmail tools"""
        return [
            GetEmailTool(self.gmail_service),
            SearchEmailsTool(self.gmail_service),
            SendEmailTool(self.gmail_service),
            DraftEmailTool(self.gmail_service),
            ReplyEmailTool(self.gmail_service),
            ForwardEmailTool(self.gmail_service),
            DeleteEmailTool(self.gmail_service),
            DownloadAttachmentTool(self.gmail_service)
        ]

    def _create_system_prompt(self) -> str:
        """Create system prompt that encourages planning and execution"""
        tool_descriptions = []
        for tool in self.tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")

        return dedent(
            f"""You are a Gmail assistant that helps users with email operations. You have access to the following Gmail tools:

            {', '.join(tool_descriptions)}
            
            When handling user requests:
            
            1. **THINK STEP BY STEP**: Break down complex requests into individual Gmail operations
            2. **PLAN YOUR APPROACH**: Identify what tools you need and in what order
            3. **EXECUTE SYSTEMATICALLY**: Use tools one by one, checking results before proceeding
            4. **HANDLE DEPENDENCIES**: When one operation depends on another (like forwarding an email you just sent), use the output from the first operation
            5. **BE THOROUGH**: Make sure to complete all parts of the user's request
            6. **PROVIDE CLEAR UPDATES**: Explain what you're doing and the results
            7. **UNRELATED REQUESTS**: If the user asks any information that sounds unrelated to gmail , try to find the information in their emails first before saying you can't help.
                                        Example: "What's the address of my dentist?" -> Search for emails from dentist and extract address from there.
            8. **EMAIL SEARCH**: When searching for emails, if you can't find any emails matching the criteria, try to search again with relaxed criteria (e.g., fewer filters, broader date range) or a different search term.
                                    If you still can't find any emails, inform the user that no matching emails were found.
            9. **FINAL SUMMARY**: At the end, summarize what actions were taken and their outcomes.
                                    Always include the message ID's and thread ID's of emails along with whatever information or action is requested as the user might need it for another operation.
                                
            
            For multi-step operations:
            - Send an email first, then use the returned message_id for forwarding/replying
            - Check email details before performing operations on them
            - Handle errors gracefully and inform the user
            
            **ALWAYS ASK CONFIRMATION** Before sending, deleting, or making any irreversible changes to emails, always ask the user for confirmation.
            
            Always aim to fully complete the user's request using the available Gmail tools.
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

    @staticmethod
    def _check_success(tool_outputs: List[Dict[str, Any]]) -> bool:
        """Check if the agent execution was successful based on tool outputs"""
        return len(tool_outputs) > 0 and not tool_outputs[-1]["content"].startswith("Error: ")

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


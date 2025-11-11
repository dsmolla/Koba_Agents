import logging
from abc import ABC, abstractmethod
from typing import Optional

from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent

from . import agent_executor
from .response import AgentResponse

load_dotenv()

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    @classmethod
    @property
    @abstractmethod
    def name(cls):
        pass

    @classmethod
    @property
    @abstractmethod
    def description(cls):
        pass

    def __init__(
            self,
            llm: BaseChatModel,
            config: Optional[RunnableConfig] = None,
            print_steps: Optional[bool] = False
    ):
        logger.info(f"Initializing {self.name}", extra={
            'agent_name': self.name,
            'llm_model': llm.model_name if hasattr(llm, 'model_name') else 'unknown',
        })
        self.llm = llm
        self.config = config
        self.print_steps = print_steps

        self.tools = self._get_tools()
        logger.debug(f"Tools loaded for {self.name}", extra={
            'agent_name': self.name,
            'tool_count': len(self.tools),
            'tool_names': [tool.name for tool in self.tools]
        })

        self.agent = self._create_agent()
        logger.info(f"{self.name} initialized successfully", extra={
            'agent_name': self.name,
            'tool_count': len(self.tools)
        })

    @abstractmethod
    def _get_tools(self) -> list[BaseTool]:
        pass

    @abstractmethod
    def system_prompt(self) -> str:
        pass

    def get_available_tools(self) -> list[dict[str, str]]:
        return [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in self.tools
        ]

    def _create_agent(self) -> CompiledStateGraph:
        return create_react_agent(
            self.llm,
            self.tools,
            name=self.name,
            prompt=SystemMessage(self.system_prompt())
        )

    def execute(self, messages: list[BaseMessage]) -> AgentResponse:
        return agent_executor.execute(
            agent=self.agent,
            messages=messages,
            print_steps=self.print_steps,
            config=self.config,
        )

    async def aexecute(self, messages: list[BaseMessage]) -> AgentResponse:
        """Async version of execute() method."""
        return await agent_executor.aexecute(
            agent=self.agent,
            messages=messages,
            print_steps=self.print_steps,
            config=self.config,
        )

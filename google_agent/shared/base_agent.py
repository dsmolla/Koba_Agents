from abc import ABC, abstractmethod
from typing import Optional

from dotenv import load_dotenv
from google_client.api_service import APIServiceLayer
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.graph.state import CompiledStateGraph
from langchain.agents import create_agent
from langgraph_supervisor import create_supervisor

from . import agent_executor
from .response import AgentResponse

load_dotenv()


class BaseGoogleAgent(ABC):
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
            google_service: APIServiceLayer,
            config: Optional[RunnableConfig] = None,
            **kwargs
    ):
        self.llm = llm
        self.google_service = google_service
        self.config = config

        for key, value in kwargs.items():
            setattr(self, key, value)

    @abstractmethod
    def system_prompt(self) -> str:
        pass

    @abstractmethod
    def agent(self) -> CompiledStateGraph:
        pass

    def execute(self, messages: list[BaseMessage]) -> AgentResponse:
        return agent_executor.execute(
            agent=self.agent(),
            messages=messages,
            config=self.config,
        )

    async def aexecute(self, messages: list[BaseMessage]) -> AgentResponse:
        return await agent_executor.aexecute(
            agent=self.agent(),
            messages=messages,
            config=self.config,
        )


class BaseReActAgent(BaseGoogleAgent, ABC):
    def __init__(
            self,
            llm: BaseChatModel,
            google_service: APIServiceLayer,
            config: Optional[RunnableConfig] = None,
            **kwargs
    ):
        super().__init__(llm, google_service, config, **kwargs)
        self._agent = None

    @abstractmethod
    def tools(self) -> list[BaseTool]:
        pass

    def get_available_tools(self) -> list[dict[str, str]]:
        return [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in self.tools()
        ]

    def agent(self) -> CompiledStateGraph:
        if self._agent is None:
            self._agent = create_agent(
                model=self.llm,
                tools=self.tools(),
                name=self.name,
                system_prompt=self.system_prompt()
            )

        return self._agent


class BaseSupervisorAgent(BaseGoogleAgent, ABC):
    def __init__(
            self,
            llm: BaseChatModel,
            google_service: APIServiceLayer,
            config: Optional[RunnableConfig] = None,
            **kwargs
    ):
        super().__init__(llm, google_service, config, **kwargs)
        self._agent = None

    @abstractmethod
    def agents(self) -> list[BaseGoogleAgent]:
        pass

    def tools(self) -> list[BaseTool]:
        return []

    def get_available_agents(self) -> list[dict[str, str]]:
        return [
            {
                "name": agent.name,
                "description": agent.description
            }
            for agent in self.agents()
        ]

    def get_available_tools(self) -> list[dict[str, str]]:
        return [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in self.tools()
        ]

    def agent(self) -> CompiledStateGraph:
        if self._agent is None:
            self._agent = create_supervisor(
                model=self.llm,
                agents=[a.agent() for a in self.agents()],
                tools=self.tools(),
                supervisor_name="supervisor_" + self.name,
                prompt=SystemMessage(self.system_prompt()),
                output_mode="last_message"
            ).compile(name=self.name)

        return self._agent

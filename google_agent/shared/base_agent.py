import inspect
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from google_client.api_service import APIServiceLayer
from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import ArgsSchema
from langchain_core.tools import BaseTool
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, Field

from . import agent_executor
from .response import AgentResponse

load_dotenv()

logger = logging.getLogger(__name__)


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
            google_service: APIServiceLayer,
            llm: BaseChatModel,
            config: Optional[RunnableConfig] = None
    ):
        self.google_service = google_service
        self.llm = llm
        self.config = config
        self._system_prompt = None
        self._tools = None
        self._agent = None
        logger.info(f"Agent initialized: {self.name}, <{llm.name}>")

    @property
    def tools(self) -> list[BaseTool]:
        return []

    @property
    @abstractmethod
    def agent(self) -> CompiledStateGraph:
        pass

    @property
    def checkpointer(self):
        return None

    @property
    def system_prompt(self) -> str:
        if self._system_prompt is None:
            tool_descriptions = []
            for tool in self.tools:
                tool_descriptions.append(f"- {tool.name}: {tool.description}")

            child_module = inspect.getfile(self.__class__)
            system_prompt = PromptTemplate.from_file(str(Path(child_module).parent / "system_prompt.txt"))
            self._system_prompt = system_prompt.format(tools='\n'.join(tool_descriptions))
        return self._system_prompt

    def execute(self, messages: list[BaseMessage]) -> AgentResponse:
        return agent_executor.execute(
            agent=self.agent,
            messages=messages,
            config=self.config,
        )

    async def aexecute(self, messages: list[BaseMessage]) -> AgentResponse:
        return await agent_executor.aexecute(
            agent=self.agent,
            messages=messages,
            config=self.config,
        )


class BaseReactGoogleAgent(BaseGoogleAgent, ABC):

    @property
    @abstractmethod
    def tools(self) -> list[BaseTool]:
        pass

    @property
    def agent(self) -> CompiledStateGraph:
        if self._agent is None:
            self._agent = create_agent(
                name=self.name,
                model=self.llm,
                tools=self.tools,
                system_prompt=self.system_prompt,
                checkpointer=self.checkpointer,
            )
        return self._agent


class AgentInput(BaseModel):
    task_description: str = Field(description="A detailed description of the task.")


def agent_to_tool(agent: BaseGoogleAgent) -> BaseTool:
    class Tool(BaseTool):
        name: str = f"delegate_to_{agent.name.lower()}"
        description: str = agent.description
        args_schema: ArgsSchema = AgentInput

        def _run(self, task_description: str) -> str:
            response = agent.execute([HumanMessage(content=task_description)])
            return response.messages[-1].content

        async def _arun(self, task_description: str) -> str:
            response = await agent.aexecute([HumanMessage(content=task_description)])
            return response.messages[-1].content

    return Tool()


class BaseSupervisorGoogleAgent(BaseGoogleAgent, ABC):
    def __init__(
            self,
            google_service: APIServiceLayer,
            llm: BaseChatModel,
            config: Optional[RunnableConfig] = None
    ):
        super().__init__(google_service, llm, config)
        self._sub_agent_tools = None
        self._sub_agents = None

    @property
    @abstractmethod
    def sub_agents(self) -> list[BaseGoogleAgent]:
        pass

    @property
    def sub_agent_tools(self) -> list[BaseTool]:
        if self._sub_agent_tools is None:
            self._sub_agent_tools = [agent_to_tool(agent) for agent in self.sub_agents]
        return self._sub_agent_tools

    @property
    def agent(self) -> CompiledStateGraph:
        if self._agent is None:
            self._agent = create_agent(
                name=self.name,
                model=self.llm,
                tools=self.tools + self.sub_agent_tools,
                system_prompt=self.system_prompt,
                checkpointer=self.checkpointer,
            )
        return self._agent

import logging
from abc import ABC, abstractmethod
from typing import Annotated

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import ArgsSchema
from langchain_core.tools import BaseTool, InjectedToolArg
from langgraph.checkpoint.base import BaseCheckpointSaver
from pydantic import BaseModel, Field

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
            model: BaseChatModel,
            tools: list[BaseTool],
            system_prompt: str,
            checkpointer: BaseCheckpointSaver = None,
    ):
        self.agent = create_agent(
            name=self.name,
            model=model,
            tools=tools,
            system_prompt=system_prompt,
            checkpointer=checkpointer,
        )

    async def arun(self, task: str, config: RunnableConfig):
        input = {"messages": [("user", task)]}
        result = await self.agent.ainvoke(input, config=config)
        print(result)
        print('--------')
        print()
        return result["messages"][-1].content


class AgentInput(BaseModel):
    task_description: str = Field(description="A detailed description of the task.")


def agent_to_tool(agent: BaseAgent) -> BaseTool:
    class Tool(BaseTool):
        name: str = f"delegate_to_{agent.name}"
        description: str = agent.description
        args_schema: ArgsSchema = AgentInput

        def _run(self, task_description: str) -> str:
            raise NotImplementedError("Use async execution.")

        async def _arun(self, task_description: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
            return await agent.arun(task_description, config)

    return Tool()

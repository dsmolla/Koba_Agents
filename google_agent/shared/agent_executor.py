import time

from langchain_core.messages import BaseMessage, AIMessage, ToolMessage
from langgraph.graph.state import CompiledStateGraph

from .exceptions import AgentException
from .response import AgentResponse

def execute(
        agent: CompiledStateGraph,
        messages: list[BaseMessage],
        config: dict = None
) -> AgentResponse:
    start = time.time()
    message_history = []

    for chunk in agent.stream({'messages': messages}, stream_mode='values', config=config):
        try:
            response = chunk['messages'][-1]
            message_history.append(response)

        except Exception as e:
            raise AgentException(message=f"Agent execution failed: {str(e)}", agent_name=agent.name)

    return AgentResponse(name=agent.name, messages=message_history)


async def aexecute(
        agent: CompiledStateGraph,
        messages: list[BaseMessage],
        config: dict = None
) -> AgentResponse:
    """Async version of execute() function."""
    start = time.time()
    message_history = []

    async for chunk in agent.astream({'messages': messages}, stream_mode='values', config=config):
        try:
            response = chunk['messages'][-1]
            message_history.append(response)

        except Exception as e:
            raise AgentException(message=f"Agent execution failed: {str(e)}", agent_name=agent.name)

    return AgentResponse(name=agent.name, messages=message_history)

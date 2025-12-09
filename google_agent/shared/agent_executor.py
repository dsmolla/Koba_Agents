import logging
import time

from langchain_core.messages import BaseMessage, AIMessage, ToolMessage
from langgraph.graph.state import CompiledStateGraph
from langchain_core.runnables import RunnableConfig

from .exceptions import AgentException
from .response import AgentResponse

logger = logging.getLogger(__name__)


def log_execution(response: BaseMessage, agent_name: str):
    if isinstance(response, AIMessage):
        logger.info(f"AI response received", extra={
            'agent_name': agent_name,
            'response_agent': response.name,
            'content_length': len(response.content) if response.content else 0,
            'tool_call_count': len(response.tool_calls) if response.tool_calls else 0,
            'content_preview': response.content[:200] if response.content else ""

        })
        logger.debug(f"{agent_name} AI response full content:\n{response.content}")

        if response.tool_calls:
            for tool_call in response.tool_calls:
                logger.info(f"Tool call initiated", extra={
                    'agent_name': response.name,
                    'tool_name': tool_call.get('name', 'unknown'),
                    'tool_id': tool_call.get('id', 'unknown'),
                    'tool_args': tool_call.get('args', {})
                })
                logger.debug(f"Tool call [{tool_call.get('name', 'unknown')}]\nArgs:\n{tool_call.get('args', {})}")

    elif isinstance(response, ToolMessage):
        logger.info(f"Tool response received", extra={
            'agent_name': agent_name,
            'tool_name': response.name,
            'content_length': len(str(response.content)) if response.content else 0,
            'content_preview': str(response.content)[:200] if response.content else ""
        })
        logger.debug(f"{agent_name} Tool response full content:\n{response.content}")

def log_error(agent_name: str, message_history: list[BaseMessage], execution_time: float, error: Exception):
    logger.error("Agent execution failed", extra={
        'agent_name': agent_name,
        'messages_processed': len(message_history),
        'message_history_preview': [str(msg.content)[:100] for msg in message_history if msg.content],
        'execution_time': f"{execution_time:.3f}s",
        'error': str(error),
    }, exc_info=True)

def log_completion(agent_name: str, message_history: list[BaseMessage], execution_time: float):
    logger.info("Agent execution completed", extra={
        'agent_name': agent_name,
        'message_history_preview': [str(msg.content)[:100] for msg in message_history if msg.content],
        'messages_generated': len(message_history),
        'execution_time': f"{execution_time:.3f}s"
    })


def execute(
        agent: CompiledStateGraph,
        messages: list[BaseMessage],
        config: dict = None
) -> AgentResponse:
    start = time.time()
    message_history = []

    logger.info("Agent execution started", extra={
        'agent_name': agent.name,
        'message_count': len(messages)
    })

    try:
        for chunk in agent.stream(input={'messages': messages}, stream_mode='values', config=config):
            response = chunk['messages'][-1]
            message_history.append(response)
            log_execution(response, agent.name)
    except Exception as e:
        execution_time = time.time() - start
        log_error(agent.name, message_history, execution_time, e)
        raise AgentException(message=f"Agent execution failed: {str(e)}", agent_name=agent.name)

    execution_time = time.time() - start
    log_completion(agent.name, message_history, execution_time)

    return AgentResponse(name=agent.name, messages=message_history)


async def aexecute(
        agent: CompiledStateGraph,
        messages: list[BaseMessage],
        config: RunnableConfig = None
) -> AgentResponse:

    logger.info(f"Agent execution started (async)", extra={
        'agent_name': agent.name,
        'message_count': len(messages),
        'content_preview': [str(msg.content)[:100] for msg in messages if msg.content]
    })

    start = time.time()
    message_history = []
    structured_responses = []

    try:
        async for chunk in agent.astream(input={'messages': messages}, stream_mode='values', config=config):
            response = chunk['messages'][-1]
            message_history.append(response)
            if chunk.get('structured_response'):
                structured_responses.append(chunk['structured_response'])

            log_execution(response, agent.name)

    except Exception as e:
        execution_time = time.time() - start
        log_error(agent.name, message_history, execution_time, e)
        raise AgentException(message=f"Agent execution failed: {str(e)}", agent_name=agent.name)

    execution_time = time.time() - start
    log_completion(agent.name, message_history, execution_time)

    return AgentResponse(name=agent.name, messages=message_history, structured_responses=structured_responses)

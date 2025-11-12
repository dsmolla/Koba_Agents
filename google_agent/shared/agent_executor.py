import logging
import time

from langchain_core.messages import BaseMessage, AIMessage, ToolMessage
from langgraph.graph.state import CompiledStateGraph

from .exceptions import AgentException
from .response import AgentResponse

logger = logging.getLogger(__name__)

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

    for chunk in agent.stream({'messages': messages}, stream_mode='values', config=config):
        try:
            response = chunk['messages'][-1]

            message_history.append(response)

            if isinstance(response, AIMessage):
                logger.debug(f"{response.name} [Agent] response", extra={
                    'agent_name': agent.name,
                    'response_agent': response.name,
                    'has_content': bool(response.content),
                    'content_length': len(response.content) if response.content else 0,
                    'tool_call_count': len(response.tool_calls) if response.tool_calls else 0
                })

                if response.content:
                    logger.debug(f"Agent content: {response.content[:200]}", extra={
                        'agent_name': response.name,
                        'full_content_length': len(response.content)
                    })

                if response.tool_calls:
                    for tool_call in response.tool_calls:
                        logger.info("Tool call initiated", extra={
                            'agent_name': response.name,
                            'tool_name': tool_call.get('name', 'unknown'),
                            'tool_id': tool_call.get('id', 'unknown'),
                            'tool_args': tool_call.get('args', {})
                        })

            elif isinstance(response, ToolMessage):
                content_preview = str(response.content)[:200] if response.content else ""
                logger.info(f"{response.name} [Tool] result", extra={
                    'agent_name': agent.name,
                    'tool_name': response.name,
                    'content_length': len(str(response.content)) if response.content else 0,
                    'content_preview': content_preview
                })

        except Exception as e:
            execution_time = time.time() - start
            logger.error("Agent execution failed", extra={
                'agent_name': agent.name,
                'execution_time': f"{execution_time:.3f}s",
                'error': str(e),
                'messages_processed': len(message_history)
            }, exc_info=True)
            raise AgentException(message=f"Agent execution failed: {str(e)}", agent_name=agent.name)

    execution_time = time.time() - start
    logger.info("Agent execution completed", extra={
        'agent_name': agent.name,
        'execution_time': f"{execution_time:.3f}s",
        'messages_generated': len(message_history)
    })

    return AgentResponse(name=agent.name, messages=message_history)


async def aexecute(
        agent: CompiledStateGraph,
        messages: list[BaseMessage],
        config: dict = None
) -> AgentResponse:
    """Async version of execute() function."""
    start = time.time()
    message_history = []

    logger.info("Agent execution started (async)", extra={
        'agent_name': agent.name,
        'message_count': len(messages)
    })

    async for chunk in agent.astream({'messages': messages}, stream_mode='values', config=config):
        try:
            response = chunk['messages'][-1]

            message_history.append(response)

            if isinstance(response, AIMessage):
                logger.debug(f"{response.name} [Agent] response", extra={
                    'agent_name': agent.name,
                    'response_agent': response.name,
                    'has_content': bool(response.content),
                    'content_length': len(response.content) if response.content else 0,
                    'tool_call_count': len(response.tool_calls) if response.tool_calls else 0
                })

                if response.content:
                    logger.debug(f"Agent content: {response.content[:200]}", extra={
                        'agent_name': response.name,
                        'full_content_length': len(response.content)
                    })

                if response.tool_calls:
                    for tool_call in response.tool_calls:
                        logger.info("Tool call initiated", extra={
                            'agent_name': response.name,
                            'tool_name': tool_call.get('name', 'unknown'),
                            'tool_id': tool_call.get('id', 'unknown'),
                            'tool_args': tool_call.get('args', {})
                        })

            elif isinstance(response, ToolMessage):
                content_preview = str(response.content)[:200] if response.content else ""
                logger.info(f"{response.name} [Tool] result", extra={
                    'agent_name': agent.name,
                    'tool_name': response.name,
                    'content_length': len(str(response.content)) if response.content else 0,
                    'content_preview': content_preview
                })

        except Exception as e:
            execution_time = time.time() - start
            logger.error("Agent execution failed (async)", extra={
                'agent_name': agent.name,
                'execution_time': f"{execution_time:.3f}s",
                'error': str(e),
                'messages_processed': len(message_history)
            }, exc_info=True)
            raise AgentException(message=f"Agent execution failed: {str(e)}", agent_name=agent.name)

    execution_time = time.time() - start
    logger.info("Agent execution completed (async)", extra={
        'agent_name': agent.name,
        'execution_time': f"{execution_time:.3f}s",
        'messages_generated': len(message_history)
    })

    return AgentResponse(name=agent.name, messages=message_history)

from langchain_core.messages import BaseMessage, AIMessage, ToolMessage
from langgraph.graph.state import CompiledStateGraph

from shared.exceptions import AgentException
from shared.response import AgentResponse


def execute(
        agent: CompiledStateGraph,
        messages: list[BaseMessage],
        print_steps: bool = False,
        config: dict = None
) -> AgentResponse:
    message_history = []

    for chunk in agent.stream({'messages': messages}, stream_mode='values', config=config):
        try:
            response = chunk['messages'][-1]

            message_history.append(response)

            if isinstance(response, AIMessage):
                if print_steps:
                    if response.content:
                        print(f"Agent Output - {response.name}: {response.content}")
                    if response.tool_calls:
                        print(f"Tool calls - {response.name}:")
                        for tool_call in response.tool_calls:
                            print(tool_call)

            elif isinstance(response, ToolMessage):
                if print_steps:
                    print(f"Tool output - {response.name}: {response.content}")

            if print_steps:
                print("-----\n")

        except Exception as e:
            raise AgentException(message=f"Agent execution failed: {str(e)}", agent_name=agent.name)

    return AgentResponse(name=agent.name, messages=message_history)

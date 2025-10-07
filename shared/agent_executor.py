from langchain_core.messages import BaseMessage, AIMessage, ToolMessage
from langgraph.graph.state import CompiledStateGraph

from shared.exceptions import AgentException
from shared.response import AgentResponse
import time

def execute(
        agent: CompiledStateGraph,
        messages: list[BaseMessage],
        print_steps: bool = False,
        config: dict = None
) -> AgentResponse:
    start = time.time()
    message_history = []

    for chunk in agent.stream({'messages': messages}, stream_mode='values', config=config):
        try:
            response = chunk['messages'][-1]

            message_history.append(response)

            if isinstance(response, AIMessage):
                if print_steps:
                    print(f"--------------------------- {response.name} [Agent] ---------------------------")
                    if response.content:
                        print(response.content)
                    if response.tool_calls:
                        print(f"Tool calls:")
                        for tool_call in response.tool_calls:
                            print(tool_call)
                    print()

            elif isinstance(response, ToolMessage):
                if print_steps:
                    print(f"--------------------------- {response.name} [Tool] ---------------------------")
                    print(response.content)
                    print()

        except Exception as e:
            raise AgentException(message=f"Agent execution failed: {str(e)}", agent_name=agent.name)

    print(f"Time taken: {round(time.time() - start, 3)}s")

    return AgentResponse(name=agent.name, messages=message_history)

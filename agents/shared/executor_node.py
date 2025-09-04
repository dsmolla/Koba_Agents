from .states import WorkflowState
from typing import Any


def compile_final_result(step_results: list[Any], plan: list[dict[str, Any]]) -> Any:
    """
    Compiles the individual step results into a final cohesive result for the agent.

    Args:
        step_results: List of results from each executed step
        plan: The original execution plan with step details

    Returns:
        The compiled final result for this agent
    """

    # Simple compilation - just return the last result
    if not step_results:
        return "No results produced"

    # If only one step, return its result
    if len(step_results) == 1:
        return step_results[0]

    # For multiple steps, create a structured result
    compiled = {
        "summary": f"Completed {len(step_results)} steps successfully",
        "step_outputs": [],
        "final_output": step_results[-1]  # Last step is usually the final product
    }

    # Add each step's result with context
    for i, (result, step) in enumerate(zip(step_results, plan)):
        compiled["step_outputs"].append({
            "step_id": step.get("step_id", i + 1),
            "description": step.get("description", f"Step {i + 1}"),
            "result": result
        })

    return compiled


def create_executor_node(agent_name: str, tools: dict):
    """Creates an executor node that runs in a loop"""

    def executor_node(state: WorkflowState) -> WorkflowState:
        agent_state = state["agent_states"][agent_name]

        # Check if execution is complete
        if agent_state["execution_complete"]:
            return state

        current_step_idx = agent_state["current_step"]
        plan = agent_state["plan"]

        # Check if all steps are completed
        if current_step_idx >= len(plan):
            # Mark execution as complete and compile final result
            final_result = compile_final_result(agent_state["step_results"], plan)

            updated_agent_state = {
                **agent_state,
                "execution_complete": True,
                "final_result": final_result
            }

            agent_states = state["agent_states"].copy()
            agent_states[agent_name] = updated_agent_state

            return {**state, "agent_states": agent_states}

        # Execute current step
        current_step = plan[current_step_idx]
        step_result = execute_step(current_step, agent_state["step_results"], tools)

        # Update agent state
        updated_agent_state = {
            **agent_state,
            "current_step": current_step_idx + 1,
            "step_results": agent_state["step_results"] + [step_result]
        }

        agent_states = state["agent_states"].copy()
        agent_states[agent_name] = updated_agent_state

        return {**state, "agent_states": agent_states}

    return executor_node


def execute_step(step: dict, previous_results: list[Any], tools: dict) -> Any:
    """Execute a single step of the plan"""

    execution_prompt = f"""
    Execute this step: {step['description']}

    Tool to use: {step['tool']}
    Expected output: {step['expected_output']}

    Previous step results available:
    {previous_results}

    Use the specified tool and return the result.
    """

    tool_name = step['tool']
    if tool_name in tools:
        result = tools[tool_name](execution_prompt, previous_results)
    else:
        result = f"Executed: {step['description']}"  # Fallback

    return result

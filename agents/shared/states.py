from typing import TypedDict, Any


class AgentState(TypedDict):
    agent_prompt: str           # The prompt given to this agent
    plan: list[dict[str, Any]]  # The execution plan from the planner
    current_step: int           # Which step the executor is currently on
    step_results: list[Any]     # Results from completed steps
    execution_complete: bool    # Whether this agent finished all steps
    final_result: Any           # The agent's final compiled result


class WorkflowState(TypedDict):
    request: str
    execution_plan: dict
    current_task_idx: int
    current_task: dict
    enhanced_prompt: str
    task_results: dict[str, Any]
    agent_states: dict[str, AgentState]
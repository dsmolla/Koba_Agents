from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from . states import WorkflowState, AgentState
from textwrap import dedent
import json


def create_planner_node(agent_name: str, agent_capabilities: list[str], llm: BaseChatModel):
    """Creates a planner node for a specific agent"""

    def planner_node(state: WorkflowState) -> WorkflowState:
        prompt = state["enhanced_prompt"]

        system_prompt = dedent(
            f"""
            You are the planner for {agent_name} with these capabilities:
            {agent_capabilities}
    
            You will create a detailed execution plan. 
            Break the task down into specific steps that can be executed sequentially.
    
            Return your plan as a JSON array of steps:
            [
                {{
                    "step_id": 1,
                    "description": "What to do in this step",
                    "tool": "which tool or agent to use",
                    "expected_output": "what this step should produce",
                    "dependencies": ["previous step outputs needed"]
                }},
                ...
            ]
    
            Make each step atomic and executable.
            """)

        # Get plan from LLM
        messages = [
            {"role": "system", "content": system_prompt},
            {"messages": HumanMessage(content=prompt)}
        ]
        plan_response = llm.invoke(messages)
        plan = json.loads(plan_response["messages"][-1].content)

        # Initialize agent state
        agent_state = AgentState(
            agent_prompt=prompt,
            plan=plan,
            current_step=0,
            step_results=[],
            execution_complete=False,
            final_result=None
        )

        agent_states = state["agent_states"].copy()
        agent_states[agent_name] = agent_state

        return {**state, "agent_states": agent_states}

    return planner_node
from textwrap import dedent
from typing import Literal, TypedDict, Optional

from google_client.services.gmail import GmailApiService

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, BaseMessage, SystemMessage, AIMessage, ToolMessage
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.types import Command
from pydantic import BaseModel, Field

from shared.constants import MODELS
from shared.exceptions import AgentException
from shared.rate_limiter import gmail_rate_limiter
from .email.agent import EmailAgent
from .labels.agent import LabelsAgent
from .thread.agent import ThreadAgent

from langchain_core.globals import set_debug


set_debug(True)

MEMBERS = ['email_agent', 'labels_agent', 'thread_agent']
LLM = ChatAnthropic(model_name=MODELS['anthropic']['haiku'])


class Task(BaseModel):
    agent: Literal[*MEMBERS, END] = Field("The agent to complete the task.")
    task: str = Field(description="A detailed description of the task to complete.")
    input: Optional[str] = Field(None, description="Any input(s) or context this agent needs that was outputted from a previous agent")
    output: Optional[AIMessage] = Field(None, description="Any output(s)", init=False)

class Plan(BaseModel):
    tasks: list[Task] = Field(description="A list of tasks to complete.")

class State(BaseModel):
    messages: list[BaseMessage]
    tasks: Optional[list[Task]] = None
    current_task_idx: int = Field(default=0, description="The current task index.", init=False)


class GmailAgent:
    name: str = "gmail_agent"

    def __init__(self, gmail_service: GmailApiService, llm: BaseChatModel = LLM, debug: bool = False):
        self.llm = llm
        self.debug = debug

        self.email_agent = EmailAgent(gmail_service, llm, debug=self.debug)
        self.labels_agent = LabelsAgent(gmail_service, llm, debug=self.debug)
        self.thread_agent = ThreadAgent(gmail_service, llm, debug=self.debug)

        research_builder = StateGraph(State)
        research_builder.add_node("planner", self.planner_node)
        research_builder.add_node("email_agent", self.email_node)
        research_builder.add_node("labels_agent", self.labels_node)
        research_builder.add_node("thread_agent", self.thread_node)
        research_builder.add_node("response_agent", self.response_node)

        research_builder.set_entry_point("planner")
        research_builder.set_finish_point("response_agent")
        self.research_graph = research_builder.compile()


    @staticmethod
    def _get_planner_system_prompt():
        return dedent(
            f"""
            You are a helpful gmail supervisor assistant tasked with managing a conversation between
            the following workers: {", ".join(MEMBERS)}
            
            Below is the capabilities of each worker:
            1. email_agent:
                - send email
                - create draft
                - reply
                - forward
                - delete email
                - search
                - download attachments

            2. labels_agent:
                - list labels
                - create label
                - add label to email
                - remove label from email
                - rename label
                - delete label

            3. thread_agent:
                - search
                - get thread details
                - summarize thread

            You're task is to distribute the work between these agents or workers.
            You will need to first break down the task into steps in the following format:
            [{{ "agent": "___", "task": "___", "input": "___"}}, ___ ]

            "agent": should only be one of {", ".join(MEMBERS)}
            "task": a detailed description of what the agent should do
            "input": any output from previous agent/worker execution this agent might need
            
            Example:
                User: Find all emails from boss@gmail.com and label them as project-1, project-2 or other depending on the content of the email.
                AI:
                    [
                    {{"agent": "email_agent", "task": "Find all emails from boss@gmail.com and classify them as project-1, project-2 or other depending on the content of the email"}},
                    {{"agent": "labels_agent", "task": "Mark the emails from email_agent according to the classification provided", "input": "email classification from email_agent"}}
                    ]
            """
        )

    def planner_node(self, state:State) -> Command[Literal[*MEMBERS]]:
        messages = [SystemMessage(self._get_planner_system_prompt())] + state.messages
        response = self.llm.with_structured_output(Plan).invoke(messages)
        plan = Plan.model_validate(response)

        return Command(
            update={"tasks": plan.tasks},
            goto=plan.tasks[0].agent
        )

    def email_node(self, state: State) -> Command[Literal[*MEMBERS, "response_agent"]]:
        current_task_idx = state.current_task_idx
        current_item = state.tasks[current_task_idx]
        current_task = current_item.task
        message = f"Your task is: {current_task}\n"
        if current_item.input:
            message += f"Context:\n{state.tasks[:current_task_idx]}"

        result = self.email_agent.execute(message)
        final_response = result['final_response']
        current_item.output = HumanMessage(content=final_response, name='email_agent')
        current_task_idx += 1

        return Command(
            update={"tasks": state.tasks, "current_task_idx": current_task_idx},
            goto=state.tasks[current_task_idx].agent if current_task_idx < len(state.tasks) else "response_agent"
        )

    def labels_node(self, state: State) -> Command[Literal[*MEMBERS, "response_agent"]]:
        current_task_idx = state.current_task_idx
        current_item = state.tasks[current_task_idx]
        current_task = current_item.task
        message = f"Your task is: {current_task}\n"
        if current_item.input:
            message += f"Context:\n{state.tasks[:current_task_idx]}"

        result = self.labels_agent.execute(message)
        final_response = result['final_response']
        current_item.output = HumanMessage(content=final_response, name='labels_agent')
        current_task_idx += 1

        return Command(
            update={"tasks": state.tasks, "current_task_idx": current_task_idx},
            goto=state.tasks[current_task_idx].agent if current_task_idx < len(state.tasks) else "response_agent",
        )

    def thread_node(self, state: State) -> Command[Literal[*MEMBERS, "response_agent"]]:
        current_task_idx = state.current_task_idx
        current_item = state.tasks[current_task_idx]
        current_task = current_item.task
        message = f"Your task is: {current_task}\n"
        if current_item.input:
            message += f"Context:\n{state.tasks[:current_task_idx]}"

        result = self.thread_agent.execute(message)
        final_response = result['final_response']
        current_item.output = HumanMessage(content=final_response, name='thread_agent')
        current_task_idx += 1

        return Command(
            update={"tasks": state.tasks, "current_task_idx": current_task_idx},
            goto=state.tasks[current_task_idx].agent if current_task_idx < len(state.tasks) else "response_agent",
        )

    def response_node(self, state: State) -> Command[Literal[END]]:
        question = state.messages[-1].content
        context = []
        for task in state.tasks:
            context.append(task.output.content)
        system_prompt = dedent(
            """
            You are a helpful responder assistant. You will be given a user input and a series of outputs from other assistants
            explaining what they did to help the user. Your task is to summarize all the outputs and respond to the user.
            Always respond in first person tone.
            Your job is to just answer the users question, do not mention that you got the information from other assistants.
            The first sentence should only address the users initial question, no additional text.
            """
        )
        message = (
            f"User Question: {question}\n" +
            f"Response from other assistants:\n" +
            "-----\n".join(context)
        )

        summary = self.llm.invoke([SystemMessage(system_prompt), HumanMessage(message)])

        return Command(update={'messages': state.messages + [summary]}, goto=END)

    def execute(self, user_input: str) -> dict:
        try:
            response = self.research_graph.invoke({'messages': [HumanMessage(user_input)]})

            return {
                'tasks': response['tasks'],
                'final_response': response['messages'][-1].content,
            }

        except Exception as e:
            raise AgentException(message=f"Agent execution failed: {str(e)}", agent_name=self.name)




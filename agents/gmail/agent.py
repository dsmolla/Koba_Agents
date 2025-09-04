from textwrap import dedent
from typing import Literal, TypedDict

from google_client.services.gmail import GmailApiService

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.types import Command

from . email.agent import EmailAgent
from . labels.agent import LabelsAgent
from . process.agent import ProcessAgent
from . query.agent import QueryAgent

from langchain_core.globals import set_debug
set_debug(True)

MEMBERS = ['email_agent', 'labels_agent', 'process_agent', 'query_agent']


class State(MessagesState):
    next: str
    steps: list[dict]


class Router(TypedDict):
    next: Literal[*MEMBERS, "FINISH"]


class GmailAgent:
    def __init__(self, gmail_service: GmailApiService, llm: BaseChatModel = None):
        self.llm = llm
        if self.llm is None:
            self.llm = ChatAnthropic(model_name='claude-3-7-sonnet-20250219')

        self.email_agent = EmailAgent(gmail_service, llm).create_agent()
        self.labels_agent = LabelsAgent(gmail_service, llm).create_agent()
        self.process_agent = ProcessAgent(gmail_service, llm).create_agent()
        self.query_agent = QueryAgent(gmail_service, llm).create_agent()

        research_builder = StateGraph(State)
        research_builder.add_node("gmail_agent", self.gmail_node)
        research_builder.add_node("email_agent", self.email_node)
        research_builder.add_node("labels_agent", self.labels_node)
        research_builder.add_node("process_agent", self.process_node)
        research_builder.add_node("query_agent", self.query_node)

        research_builder.add_edge(START, "gmail_agent")
        self.research_graph = research_builder.compile()

    @staticmethod
    def _get_system_prompt():
        return dedent(
            f"""
            You are a helpful gmail supervisor assistant tasked with managing a conversation between
            the following workers: {MEMBERS}

            Given the following user request, respond with the worker to act next.
            Each worker will perform a task and respond with their results and status.
            
            When finished respond with FINISH.
            """
        )

    def planner(self, state:State):
        query = state["messages"]

        # Call LLM to create a plan
        plan_prompt = dedent(
            f"""
            You are a planner. Break down the task into steps. 
            Use JSON format like: 
            [{{"action": "...", "input": "..."}}, ...]
            Query: {query}
            """
        )

        response = self.llm.invoke(plan_prompt)
        return {"steps": response.content}

    def gmail_node(self, state: State) -> Command[Literal[*MEMBERS, "__end__"]]:
        messages = [
                       {"role": "system", "content": self._get_system_prompt()},
                   ] + state["messages"]

        response = self.llm.with_structured_output(Router).invoke(messages)
        goto = response["next"]
        if goto == "FINISH":
            goto = END

        return Command(goto=goto, update={"next": goto})

    def email_node(self, state: State) -> Command[Literal["gmail_agent"]]:
        result = self.email_agent.invoke(state)
        return Command(
            update={
                "messages": [
                    HumanMessage(content=result["messages"][-1].content, name="email_agent")
                ]
            },
            # Always report back to supervisor
            goto="gmail_agent",
        )

    def labels_node(self, state: State) -> Command[Literal["gmail_agent"]]:
        result = self.labels_agent.invoke(state)
        return Command(
            update={
                "messages": [
                    HumanMessage(content=result["messages"][-1].content, name="labels_agent")
                ]
            },
            # Always report back to supervisor
            goto="gmail_agent",
        )

    def process_node(self, state: State) -> Command[Literal["gmail_agent"]]:
        result = self.process_agent.invoke(state)
        return Command(
            update={
                "messages": [
                    HumanMessage(content=result["messages"][-1].content, name="process_agent")
                ]
            },
            # Always report back to supervisor
            goto="gmail_agent",
        )

    def query_node(self, state: State) -> Command[Literal["gmail_agent"]]:
        result = self.query_agent.invoke(state)
        return Command(
            update={
                "messages": [
                    HumanMessage(content=result["messages"][-1].content, name="query_agent")
                ]
            },
            # Always report back to supervisor
            goto="gmail_agent",
        )



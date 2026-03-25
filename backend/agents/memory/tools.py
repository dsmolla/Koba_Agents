import uuid
import logging
from typing import Annotated, Optional

from langchain_core.callbacks import adispatch_custom_event
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import ArgsSchema, InjectedToolArg, BaseTool
from pydantic import BaseModel, Field
from langgraph.store.base import BaseStore

logger = logging.getLogger(__name__)

class CreateMemoryInput(BaseModel):
    fact: str = Field(description="The core fact, preference, or detail to save about the user.")
    category: str = Field(description="The category of the fact (e.g. 'work', 'preference', 'relationship', 'general').")

class CreateMemoryTool(BaseTool):
    name: str = "create_memory"
    description: str = "Save a completely NEW persistent fact or personal preference about the user into long-term system memory. DO NOT use this if a similar fact already exists."
    args_schema: type[BaseModel] = CreateMemoryInput

    def _run(self, fact: str, category: str, config: Annotated[RunnableConfig, InjectedToolArg] = None) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(self, fact: str, category: str, config: Annotated[RunnableConfig, InjectedToolArg] = None) -> str:
        await adispatch_custom_event("tool_status", {"text": "Saving New Memory...", "icon": "🧠"})
        store: BaseStore = config["configurable"]["store"]
        thread_id = config["configurable"]["thread_id"]
        
        memory_id = str(uuid.uuid4())
        await store.aput(namespace=("memory", thread_id), key=memory_id, value={"fact": fact, "category": category})
        logger.info(f"Created memory for thread {thread_id} under key {memory_id}: {fact}")
        return "SUCCESS: Fact successfully written to long-term memory. DO NOT call this tool again for this request. The system prompt will reflect this strictly on the next turn."


class UpdateMemoryInput(BaseModel):
    memory_id: str = Field(description="The EXACT MEMORY_ID of the existing memory to update.")
    fact: str = Field(description="The updated core fact, preference, or detail to save about the user.")
    category: str = Field(description="The category of the fact (e.g. 'work', 'preference', 'relationship', 'general').")

class UpdateMemoryTool(BaseTool):
    name: str = "update_memory"
    description: str = "Overwrite or modify an EXISTING fact or preference in the user's long-term system memory using its exact MEMORY_ID. ALWAYS use this instead of create_memory if the user is changing an existing preference."
    args_schema: type[BaseModel] = UpdateMemoryInput

    def _run(self, memory_id: str, fact: str, category: str, config: Annotated[RunnableConfig, InjectedToolArg] = None) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(self, memory_id: str, fact: str, category: str, config: Annotated[RunnableConfig, InjectedToolArg] = None) -> str:
        await adispatch_custom_event("tool_status", {"text": "Updating Memory...", "icon": "🧠"})
        store: BaseStore = config["configurable"]["store"]
        thread_id = config["configurable"]["thread_id"]
        
        await store.aput(namespace=("memory", thread_id), key=memory_id, value={"fact": fact, "category": category})
        logger.info(f"Updated memory for thread {thread_id} under key {memory_id}: {fact}")
        return "SUCCESS: Fact successfully updated in long-term memory. DO NOT call this tool again. The backend database has been mutated successfully, but your local System prompt will not update until the next conversation sequence. Output your final BotMessage now."


class DeleteMemoryInput(BaseModel):
    memory_id: str = Field(description="The ID of the memory to delete.")

class DeleteMemoryTool(BaseTool):
    name: str = "delete_memory"
    description: str = "Delete an outdated or incorrect fact from the user's long-term system memory."
    args_schema: type[BaseModel] = DeleteMemoryInput

    def _run(self, memory_id: str, config: Annotated[RunnableConfig, InjectedToolArg] = None) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(self, memory_id: str, config: Annotated[RunnableConfig, InjectedToolArg] = None) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Forgetting Long-Term Memory...", "icon": "🧠"}
        )
        
        store: BaseStore = config["configurable"]["store"]
        thread_id = config["configurable"]["thread_id"]
        
        await store.adelete(
            namespace=("memory", thread_id),
            key=memory_id
        )
        
        logger.info(f"Deleted memory for thread {thread_id} under key {memory_id}")
        return "Fact successfully deleted from long-term memory."

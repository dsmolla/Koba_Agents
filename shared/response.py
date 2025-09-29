from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field


class AgentResponse(BaseModel):
    name: str = Field(..., title="Agent name")
    messages: list[BaseMessage] = Field(..., title="Message history")


class ToolResponse(BaseModel):
    status: str = Field(..., title="Status of tool execution")
    message: str = Field(..., title="Tool message")
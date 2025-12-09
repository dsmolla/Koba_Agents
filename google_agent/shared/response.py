from typing import Optional

from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field


class StructuredResponse(BaseModel):
    text: str = Field(description="The text of the response")
    requested_files: Optional[list[str]] = Field(default_factory=list, description="Path to the files requested by the user")


class AgentResponse(BaseModel):
    name: str = Field(..., title="Agent name")
    messages: list[BaseMessage] = Field(..., title="Message history")
    structured_responses: Optional[list[StructuredResponse]] = Field(
        default_factory=list,
        title="Structured responses from the main agent"
    )


class ToolResponse(BaseModel):
    status: str = Field(..., title="Status of tool execution")
    message: str = Field(..., title="Tool message")
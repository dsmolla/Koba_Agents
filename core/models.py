import time
from typing import Literal, List

from pydantic import BaseModel, Field


class FileAttachment(BaseModel):
    filename: str
    path: str
    mime_type: str
    size: int


class UserMessage(BaseModel):
    type: Literal["message"]
    sender: Literal["user"]
    content: str
    files: List[FileAttachment] = Field(default_factory=list)
    timestamp: int


class BotMessage(BaseModel):
    type: Literal["message"] = "message"
    sender: Literal["bot"] = "bot"
    content: str
    files: List[FileAttachment] = Field(default_factory=list, description="Files requested by the user")
    timestamp: int = int(time.time() * 1000)


class GoogleCredentials(BaseModel):
    token: str
    refresh_token: str | None = None
    token_uri: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    scopes: list[str] | None = None
    expiry: str | None = None

    class Config:
        extra = "allow"

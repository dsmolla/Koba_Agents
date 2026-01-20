import time
from typing import Literal, List

from pydantic import BaseModel, Field

from config import Config


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
    refresh_token: str
    client_id: str = Config.GOOGLE_OAUTH_CLIENT_ID
    client_secret: str = Config.GOOGLE_OAUTH_CLIENT_SECRET

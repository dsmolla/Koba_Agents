import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Literal, List

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field, field_validator

from agents.supervisor import SupervisorAgent
from core.db import db
from core.dependencies import get_current_user_ws, get_current_user_http, get_db
from core.exceptions import ProviderNotConnectedError


class FileAttachment(BaseModel):
    id: str
    filename: str
    path: str
    mime_type: str
    size: int


class UserMessage(BaseModel):
    type: Literal["message"]
    sender: Literal["bot", "user"]
    content: str
    files: List[FileAttachment] = Field(default_factory=list)
    timestamp: datetime

    @field_validator("timestamp", mode="before")
    def parse_timestamp(cls, v):
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v)
            except ValueError:
                raise ValueError("Invalid timestamp format")
        return v


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


load_dotenv()
LLM_FLASH = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
supervisor_agent: SupervisorAgent | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    checkpointer = await db.get_checkpointer()
    global supervisor_agent
    supervisor_agent = SupervisorAgent(model=LLM_FLASH, checkpointer=checkpointer)
    yield
    await db.disconnect()


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("uvicorn")


@app.post("/integrations/google")
async def save_google_credentials(
        creds: GoogleCredentials,
        user: Any = Depends(get_current_user_http),
        database: Any = Depends(get_db)
):
    try:
        await database.insert_provider_token(user.id, 'google', creds.model_dump())
    except Exception as e:
        logger.error(f"Failed to save credentials: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.websocket("/ws/chat")
async def websocket_endpoint(
        websocket: WebSocket,
        user: Any = Depends(get_current_user_ws)
):
    await websocket.accept()
    user_id = user.id
    timezone = websocket.query_params.get("timezone", "UTC")
    config = RunnableConfig(
        configurable={
            "thread_id": user_id,
            "timezone": timezone,
        }
    )
    logger.info(f"User {user_id} connected!")

    try:
        state_snapshot = await supervisor_agent.agent.aget_state(config)
        messages = state_snapshot.values.get("messages", [])
        history_payload = []
        for msg in messages:
            if isinstance(msg, HumanMessage) and msg.name == "RealUser":
                original_msg = msg.additional_kwargs.get("message", {})
                history_payload.append(original_msg)
            elif isinstance(msg, AIMessage) and msg.name == "SupervisorAgent":
                if msg.text and not msg.tool_calls:
                    history_payload.append(
                        {
                            'type': 'message',
                            'sender': 'bot',
                            'content': msg.text,
                            'files': [],
                            'timestamp': msg.additional_kwargs.get("timestamp", None),
                        }
                    )

        logger.info("History payload sent")
        await websocket.send_json(
            {
                "type": "history",
                "messages": history_payload,
            }
        )
    except Exception as e:
        logger.error(f"Failed to fetch messages: {e}")

    while True:
        try:
            data = await websocket.receive_json()
            logger.info(f"Received message: {data}")
            user_message = UserMessage(**data)

            full_message = user_message.content
            if user_message.files:
                full_message += "\n\n----------- Attached files -----------\n"
                for file in user_message.files:
                    full_message += "\n"
                    full_message += f"File name: {file.filename}"
                    full_message += f"File Path: {file.path}"

            input_message = HumanMessage(content=full_message, name='RealUser', additional_kwargs={'message': data})
            async for event in supervisor_agent.agent.astream_events({"messages": [input_message]}, config=config):
                kind = event["event"]
                if kind == "on_custom_event" and event["name"] == "tool_status":
                    data = event["data"]
                    logger.info(f"Tool Status sent {data['text']}")
                    await websocket.send_json(
                        {
                            "type": "status",
                            "content": data["text"],
                            "icon": data.get("icon", "⏳")
                        }
                    )
                elif kind == 'on_chain_end' and event['name'] == 'SupervisorAgent':
                    content = event['data']['output']['messages'][-1].text
                    logger.info(f"Agent Response Sent: {content}")
                    await websocket.send_json(
                        {
                            "type": "message",
                            "sender": "bot",
                            "content": content,
                            "files": [],
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
        except WebSocketDisconnect:
            logger.info(f"User {user_id} disconnected")
            break
        except ProviderNotConnectedError as e:
            logger.error(f"Failed to fetch messages: {e}")
            await websocket.send_json(
                {
                    "type": "error",
                    "code": "AUTH_REQUIRED",
                    "provider": "Google",
                    "content": "Please authenticate your Google account."
                }
            )


@app.delete("/chat/clear")
async def clear_chat(
        user: Any = Depends(get_current_user_http),
        database: Any = Depends(get_db)
):
    try:
        await database.clear_thread(user.id)
    except Exception as e:
        logger.error(f"Failed to clear chat: {e}")
        raise HTTPException(status_code=500, detail="Error occurred.")

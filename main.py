import logging
import json
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from agents.supervisor import SupervisorAgent
from agents.common.llm_models import MODELS
from core.exceptions import ProviderNotConnectedError
from core.db import db
from core.dependencies import get_current_user_ws, get_current_user_http, get_db


load_dotenv(r'C:\Users\Dagmawi\Projects\Koba_Agents\backend\.env')
LLM_FLASH = ChatGoogleGenerativeAI(model=MODELS['gemini']['flash'])

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
    allow_origins=["*"],  # Change to ["http://localhost:3000"] in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("uvicorn")


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


@app.post("/integrations/google")
async def save_google_credentials(
    creds: GoogleCredentials,
    user: Any = Depends(get_current_user_http),
    database: Any = Depends(get_db)
):
    try:
        await database.insert_provider_token(user.id, 'google', creds.model_dump())
        return {"status": "success", "message": "Google credentials saved."}
    except Exception as e:
        logger.error(f"Failed to save credentials: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# --- 3. WebSocket Endpoint (Real-time Chat) ---
@app.websocket("/ws/chat")
async def websocket_endpoint(
        websocket: WebSocket,
        user: Any = Depends(get_current_user_ws)
):
    await websocket.accept()
    user_id = str(user.id)
    timezone = websocket.query_params.get("timezone", "UTC")
    config = RunnableConfig(
        configurable={
            "thread_id": user_id,
            "timezone": timezone,
        }
    )

    while True:
        try:
            data = await websocket.receive_json()
            user_message = data.get("message")

            if not user_message:
                continue

            input_message = HumanMessage(content=user_message)
            async for event in supervisor_agent.agent.astream_events(
                    {"messages": [input_message]},
                    config=config,
            ):
                print(event)
                print('\n\n')
                kind = event["event"]
                if kind == "on_custom_event" and event["name"] == "tool_status":
                    data = event["data"]
                    await websocket.send_json({
                        "type": "status",
                        "content": data["text"],
                        "icon": data.get("icon", "⏳")
                    })
                elif kind == 'on_chain_end' and event['name'] == 'SupervisorAgent':
                    print(event)
                    content = event['data']['output']['messages'][-1].content
                    if isinstance(content, list):
                        content = content[0].get('text', "ERROR!")
                    await websocket.send_json({
                        "type": "agent_output",
                        "content": content
                    })
        except WebSocketDisconnect:
            logger.info(f"User {user_id} disconnected")
            break
        except ProviderNotConnectedError as e:
            await websocket.send_json({
                "type": "google_not_connected",
            })

@app.delete("/chat/clear")
async def clear_chat(
        user: Any = Depends(get_current_user_http),
        database: Any = Depends(get_db)
):
    """
    Nuke the conversation history.
    Since thread_id == user_id, we delete by user_id.
    """
    user_id = str(user.id)

    try:
        await database.clear_thread(user_id)
        return {"status": "deleted", "content": "Memory wiped."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



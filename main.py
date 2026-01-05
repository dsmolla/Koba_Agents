import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from agents.common.llm_models import LLM_FLASH
from agents.supervisor import SupervisorAgent
from core.db import db
from core.dependencies import get_current_user_ws, get_current_user_http, get_db


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

    try:
        while True:
            data = await websocket.receive_json()
            user_message = data.get("message")

            if not user_message:
                continue

            input_message = HumanMessage(content=user_message)
            async for event in supervisor_agent.agent.astream_events(
                    {"messages": [input_message]},
                    config=config,
                    version="v1"
            ):
                kind = event["event"]
                if kind == "on_custom_event" and event["name"] == "user_status":
                    data = event["data"]
                    await websocket.send_json({
                        "type": "status",
                        "content": data["text"],
                        "icon": data.get("icon", "⏳")
                    })
                elif kind == 'on_chain_end' and event['name'] == 'SupervisorAgent':
                    await websocket.send_json({
                        "type": "agent_output",
                        "content": event['data']['output']['messages'][-1].content[0]['text']
                    })

    except WebSocketDisconnect:
        logger.info(f"User {user_id} disconnected")
    except Exception as e:
        logger.error(f"Error in chat loop: {e}")
        try:
            await websocket.send_json({"type": "error", "content": "Internal error occurred. Try again later."})
        except:
            pass


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
        await database.clear_chat(user_id)
        return {"status": "deleted", "content": "Memory wiped."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



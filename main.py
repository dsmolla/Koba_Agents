import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver

from agents.supervisor import SupervisorAgent
from core.db import db
from core.dependencies import get_current_user_ws, get_current_user_http, get_db
from core.exceptions import ProviderNotConnectedError
from core.models import GoogleCredentials, UserMessage, BotMessage

load_dotenv()
LLM_FLASH = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
supervisor_agent: SupervisorAgent | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    checkpointer = await db.get_checkpointer()
    # checkpointer = MemorySaver()
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
                if msg.tool_calls and msg.tool_calls[0]['name'] == 'BotMessage':
                    history_payload.append(
                        BotMessage.model_validate(msg.tool_calls[0]['args']).model_dump()
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

            message_received_at = time.time()

            full_message = user_message.content
            if user_message.files:
                full_message += "\n\n----------- Attached files -----------\n"
                for file in user_message.files:
                    full_message += "\n"
                    full_message += f"File name: {file.filename}\n"
                    full_message += f"File Path: {file.path}"

            input_message = HumanMessage(content=full_message, name='RealUser', additional_kwargs={'message': data})
            async for event in supervisor_agent.agent.astream_events({"messages": [input_message]}, config=config):
                logger.info(f"Received event: \n{event}\n\n")
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
                    bot_message: BotMessage = event['data']['output']['structured_response']
                    bot_message = bot_message.model_dump()
                    logger.info(f"Agent Response Sent: {bot_message}")
                    logger.info(f"Response time: {time.time() - message_received_at}s")
                    await websocket.send_json(
                        bot_message
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

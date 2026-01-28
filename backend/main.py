import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.auth.exceptions import RefreshError
from google_client.api_service import APIServiceLayer
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI

from agents.supervisor import SupervisorAgent
from config import Config
from core.db import database
from core.dependencies import get_current_user_ws, get_current_user_http
from core.exceptions import ProviderNotConnectedError
from core.models import GoogleCredentials, UserMessage, BotMessage
from core.redis_client import redis_client
from logging_config import setup_logging

load_dotenv()
Config.validate()
setup_logging(Config.LOG_LEVEL)

logger = logging.getLogger(__name__)

LLM = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
supervisor_agent: SupervisorAgent | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    checkpointer = await database.get_checkpointer()
    global supervisor_agent
    supervisor_agent = SupervisorAgent(model=LLM, checkpointer=checkpointer)
    yield
    await database.disconnect()


app = FastAPI(lifespan=lifespan)

# TODO: Update allow_origins with specific domains for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/auth/ticket")
async def generate_ws_ticket(user: Any = Depends(get_current_user_http)):
    ticket = str(uuid.uuid4())
    await redis_client.set_ws_ticket(ticket, user.id)
    logger.info("Generated WebSocket ticket", extra={"user_id": user.id})
    return {"ticket": ticket}


@app.post("/integrations/google")
async def save_google_credentials(
        creds: GoogleCredentials,
        user: Any = Depends(get_current_user_http)
):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={creds.token}")
            if resp.status_code == 200:
                data = resp.json()
                scopes = data.get("scope", "")
            else:
                logger.warning(f"Failed to fetch token info: {resp.text}", extra={"user_id": user.id})
                scopes = ""

        creds_dict = creds.model_dump()
        creds_dict["scopes"] = scopes

        await database.set_provider_token(user.id, 'google', creds_dict)
        await redis_client.delete_provider_token(user.id, 'google')
        logger.info("Saved Google credentials", extra={"user_id": user.id, "scopes": scopes})
    except Exception as e:
        logger.error(f"Failed to save credentials: {e}", extra={"user_id": user.id}, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.get("/integrations/{provider}")
async def get_integration_status(
        provider: str,
        user: Any = Depends(get_current_user_http)
):
    try:
        creds = await database.get_provider_token(user.id, provider)
        return {"connected": True, "scopes": creds.get("scopes", "")}
    except ProviderNotConnectedError:
        return {"connected": False, "scopes": ""}
    except Exception as e:
        logger.error(f"Failed to check integration status: {e}", extra={"user_id": user.id, "provider": provider}, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.delete("/integrations/{provider}")
async def delete_integration(
        provider: str,
        user: Any = Depends(get_current_user_http)
):
    try:
        token = await database.get_provider_token(user.id, provider)
        await database.delete_provider_token(user.id, provider)
        await redis_client.delete_provider_token(user.id, provider)
        if APIServiceLayer(token).revoke_token():
            logger.info("Integration removed", extra={"user_id": user.id, "provider": provider})
            return {"message": "Integration removed"}
    except Exception as e:
        logger.error(f"Failed to remove integration: {e}", extra={"user_id": user.id, "provider": provider}, exc_info=True)
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
    logger.info(f"User connected", extra={"user_id": user_id})

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

        logger.info("History payload sent", extra={"user_id": user_id, "message_count": len(history_payload)})
        await websocket.send_json(
            {
                "type": "history",
                "messages": history_payload,
            }
        )
    except Exception as e:
        logger.error(f"Failed to fetch messages: {e}", extra={"user_id": user_id}, exc_info=True)

    while True:
        try:
            data = await websocket.receive_json()
            logger.info(f"Received message", extra={"user_id": user_id, "content_length": len(str(data))})
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
                kind = event["event"]
                # logger.info(f"Received event: {event}\n\n") # Commented out noisy log
                if kind == "on_custom_event" and event["name"] == "tool_status":
                    data = event["data"]
                    logger.info(f"Tool Status: {data['text']}", extra={"user_id": user_id})
                    await websocket.send_json(
                        {
                            "type": "status",
                            "content": data["text"],
                            "icon": data.get("icon", "⏳")
                        }
                    )
                elif kind == 'on_chain_end' and event['name'] == 'SupervisorAgent':
                    bot_message: BotMessage = event['data']['output']['structured_response']
                    bot_message_dump = bot_message.model_dump()
                    response_time = time.time() - message_received_at
                    logger.info(f"Agent Response Sent", extra={"user_id": user_id, "response_time": response_time})
                    await websocket.send_json(
                        bot_message_dump
                    )
        except WebSocketDisconnect:
            logger.info(f"User disconnected", extra={"user_id": user_id})
            break
        except ProviderNotConnectedError as e:
            logger.warning(f"Provider not connected: {e}", extra={"user_id": user_id})
            await websocket.send_json(
                {
                    "type": "error",
                    "code": "AUTH_REQUIRED",
                    "provider": "Google",
                    "content": "Please authenticate your Google account."
                }
            )
        except RefreshError as e:
            logger.warning(f"Token refresh failed: {e}", extra={"user_id": user_id})
            await websocket.send_json(
                {
                    "type": "error",
                    "code": "AUTH_EXPIRED",
                    "provider": "Google",
                    "content": "Please re-authenticate your Google account."
                }
            )


@app.delete("/chat/clear")
async def clear_chat(user: Any = Depends(get_current_user_http)):
    try:
        await database.clear_thread(user.id)
        logger.info("Chat history cleared", extra={"user_id": user.id})
    except Exception as e:
        logger.error(f"Failed to clear chat: {e}", extra={"user_id": user.id}, exc_info=True)
        raise HTTPException(status_code=500, detail="Error occurred.")

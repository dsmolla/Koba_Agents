import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from google.auth.exceptions import RefreshError
from google_client.api_service import APIServiceLayer
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI

from agents.supervisor import SupervisorAgent
from config import Config
from core.db import database
from core.auth import get_google_service
from core.dependencies import get_current_user_ws, get_current_user_http
from core.exceptions import ProviderNotConnectedError
from core.rate_limit import RateLimitMiddleware, check_ws_rate_limit
from core.models import GoogleCredentials, UserMessage, BotMessage
from core.redis_client import redis_client
from logging_config import setup_logging

load_dotenv()
Config.validate()
setup_logging(Config.LOG_LEVEL)

logger = logging.getLogger(__name__)

LLM = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
supervisor_agent: SupervisorAgent | None = None


def log_event(event, user_id):
    kind = event["event"]
    name = event.get("name", "Unknown")
    data = event.get("data", {})

    if kind == "on_chain_start" and "input" in data:
        input_data = data["input"]
        if isinstance(input_data, dict) and "messages" in input_data:
            messages = input_data["messages"]
            if messages and isinstance(messages[-1], HumanMessage) and messages[-1].name:
                logger.debug(f"{messages[-1].name}: {messages[-1].content}", extra={"user_id": user_id})

    elif kind == "on_tool_start":
        tool_name = name
        tool_args = data.get("input")
        logger.debug(f"tool_call [{tool_name}]: {tool_args}", extra={"user_id": user_id})

    elif kind == "on_tool_end":
        tool_output = data.get("output")
        logger.debug(f"tool_response [{tool_output.name}]: {tool_output.content}", extra={"user_id": user_id})

    elif kind == "on_chat_model_end":
        output = data.get("output")
        if isinstance(output, AIMessage) and output.content:
            if not output.tool_calls:
                logger.debug(f"agent_response [{output.name}]: {output.content}", extra={"user_id": user_id})

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    checkpointer = await database.get_checkpointer()
    global supervisor_agent
    supervisor_agent = SupervisorAgent(model=LLM, checkpointer=checkpointer)
    yield
    await database.disconnect()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
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

    is_connected = True
    while True:
        try:
            if not is_connected:
                break

            data = await websocket.receive_json()

            # Check rate limit
            is_allowed, remaining = await check_ws_rate_limit(user_id)
            if not is_allowed:
                logger.warning("WebSocket rate limit exceeded", extra={"user_id": user_id})
                await websocket.send_json({
                    "type": "error",
                    "code": "RATE_LIMITED",
                    "content": "Too many messages. Please wait before sending more."
                })
                continue

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Received message content: {data}", extra={"user_id": user_id})
            else:
                logger.info(f"Received message", extra={"user_id": user_id, "content_length": len(str(data))})

            user_message = UserMessage(**data)
            message_received_at = time.time()

            # Create API service once per message and pass via config
            try:
                api_service = await get_google_service(user_id, timezone)
            except (ProviderNotConnectedError, RefreshError):
                api_service = None
            message_config = RunnableConfig(
                configurable={
                    "thread_id": user_id,
                    "timezone": timezone,
                    "api_service": api_service,
                },
                recursion_limit=50
            )

            full_message = user_message.content
            if user_message.files:
                full_message += "\n\n----------- Attached files -----------\n"
                for file in user_message.files:
                    full_message += "\n"
                    full_message += f"File name: {file.filename}\n"
                    full_message += f"File Path: {file.path}"

            input_message = HumanMessage(content=full_message, name='RealUser', additional_kwargs={'message': data})
            async for event in supervisor_agent.agent.astream_events({"messages": [input_message]}, config=message_config):
                kind = event["event"]
                if logger.isEnabledFor(logging.DEBUG):
                    log_event(event, user_id)

                if kind == "on_custom_event" and event["name"] == "tool_status":
                    data = event["data"]
                    logger.info(f"Tool Status: {data['text']}", extra={"user_id": user_id})
                    
                    if is_connected:
                        try:
                            await websocket.send_json(
                                {
                                    "type": "status",
                                    "content": data["text"],
                                    "icon": data.get("icon", "⏳")
                                }
                            )
                        except (WebSocketDisconnect, RuntimeError):
                            is_connected = False
                            logger.info("User disconnected during status update. Continuing in background.", extra={"user_id": user_id})

                elif kind == 'on_chain_end' and event['name'] == 'SupervisorAgent':
                    bot_message: BotMessage = event['data']['output']['structured_response']
                    bot_message_dump = bot_message.model_dump()
                    response_time = time.time() - message_received_at
                    
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(f"Agent Response content: {bot_message_dump}", extra={"user_id": user_id, "response_time": response_time})
                    else:
                        logger.info(f"Agent Response Sent", extra={"user_id": user_id, "response_time": response_time})
                        
                    if is_connected:
                        try:
                            await websocket.send_json(
                                bot_message_dump
                            )
                        except (WebSocketDisconnect, RuntimeError):
                            is_connected = False
                            logger.info("User disconnected during final response. Saved to DB.", extra={"user_id": user_id})

        except WebSocketDisconnect:
            logger.info(f"User disconnected", extra={"user_id": user_id})
            break
        except ProviderNotConnectedError as e:
            logger.warning(f"Provider not connected: {e}", extra={"user_id": user_id})
            if is_connected:
                try:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "code": "AUTH_REQUIRED",
                            "provider": "Google",
                            "content": "Please authenticate your Google account."
                        }
                    )
                except (WebSocketDisconnect, RuntimeError):
                    is_connected = False
        except RefreshError as e:
            logger.warning(f"Token refresh failed: {e}", extra={"user_id": user_id})
            if is_connected:
                try:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "code": "AUTH_EXPIRED",
                            "provider": "Google",
                            "content": "Please re-authenticate your Google account."
                        }
                    )
                except (WebSocketDisconnect, RuntimeError):
                    is_connected = False


@app.delete("/chat/clear")
async def clear_chat(user: Any = Depends(get_current_user_http)):
    try:
        await database.clear_thread(user.id)
        logger.info("Chat history cleared", extra={"user_id": user.id})
    except Exception as e:
        logger.error(f"Failed to clear chat: {e}", extra={"user_id": user.id}, exc_info=True)
        raise HTTPException(status_code=500, detail="Error occurred.")

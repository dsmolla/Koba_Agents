import logging
import time
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from google.auth.exceptions import RefreshError
from google.genai.errors import APIError as GenAIAPIError
from langchain_google_genai._common import GoogleGenerativeAIError
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from config import Config
from core.auth import get_google_service
from core.db import database
from core.dependencies import get_current_user_ws, get_current_user_http
from core.exceptions import ProviderNotConnectedError
from core.models import UserMessage, BotMessage
from core.rate_limit import check_ws_rate_limit
from logging_config import log_event

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


async def send_chat_history(websocket: WebSocket, agent, config: RunnableConfig, user_id: str):
    """Load conversation history from LangGraph state and send to client."""
    try:
        state_snapshot = await agent.agent.aget_state(config)
        # Limit to the most recent 200 LangGraph messages to avoid loading full history
        # for long conversations (200 raw msgs ≈ 50-100 visible user/bot message pairs)
        messages = state_snapshot.values.get("messages", [])[-200:]
        history_payload = []
        for msg in messages:
            if isinstance(msg, HumanMessage) and msg.name == "RealUser":
                original_msg = msg.additional_kwargs.get("message", {})
                history_payload.append(original_msg)
            elif isinstance(msg, AIMessage) and msg.name == "SupervisorAgent":
                if msg.tool_calls and msg.tool_calls[0]['name'] == 'BotMessage':
                    args = msg.tool_calls[0]['args']
                    history_payload.append(
                        BotMessage(
                            content=args.get('content', ''),
                            files=args.get('files', []),
                        ).model_dump()
                    )

        logger.debug("History payload sent", extra={"user_id": user_id, "message_count": len(history_payload)})
        await websocket.send_json({"type": "history", "messages": history_payload})
    except Exception as e:
        logger.error(f"Failed to fetch messages: {e}", extra={"user_id": user_id}, exc_info=True)


async def process_message(
    websocket: WebSocket,
    agent,
    config: RunnableConfig,
    data: dict,
    user_id: str,
    api_service,
) -> bool:
    """Process a single user message through the agent pipeline.

    Returns False if the WebSocket disconnected during processing.
    """
    is_connected = True
    message_received_at = time.time()

    message_config = RunnableConfig(
        configurable={
            "thread_id": user_id,
            "timezone": config.get("configurable", {}).get("timezone", "UTC"),
            "api_service": api_service,
        },
        recursion_limit=50
    )

    if data.get("type") == "approval":
        input_data = Command(resume={"approved": data.get("approved", False)})
    else:
        user_message = UserMessage(**data)
        full_message = user_message.content
        if user_message.files:
            full_message += "\n\n----------- Attached files -----------\n"
            for file in user_message.files:
                full_message += "\n"
                full_message += f"File name: {file.filename}\n"
                full_message += f"File Path: {file.path}"

        input_message = HumanMessage(content=full_message, name='RealUser', additional_kwargs={'message': data})
        input_data = {"messages": [input_message]}

    interrupt_caught = False
    async for event in agent.agent.astream_events(input_data, config=message_config):
        kind = event["event"]
        if logger.isEnabledFor(logging.DEBUG):
            log_event(event, user_id)

        if kind == "on_custom_event" and event["name"] == "tool_status":
            status_data = event["data"]
            logger.debug(f"Tool Status: {status_data['text']}", extra={"user_id": user_id})

            if is_connected:
                try:
                    await websocket.send_json({
                        "type": "status",
                        "content": status_data["text"],
                        "icon": status_data.get("icon", "\u23f3")
                    })
                except (WebSocketDisconnect, RuntimeError):
                    is_connected = False
                    logger.debug("User disconnected during status update. Continuing in background.", extra={"user_id": user_id})

        elif kind == 'on_chain_stream' and event['name'] == 'SupervisorAgent':
            chunk = event['data'].get('chunk', {})
            if '__interrupt__' in chunk:
                interrupts = chunk['__interrupt__']
                if interrupts:
                    interrupt_caught = True
                    interrupt_data = interrupts[0].value
                    if is_connected:
                        try:
                            # Use .get() to prevent KeyErrors from stale LangGraph checkpoints
                            await websocket.send_json({
                                "type": "approval_required",
                                "confirmation": interrupt_data.get('confirmation', 'Action Approval Required:'),
                                "data": interrupt_data.get('data', interrupt_data)
                            })
                        except (WebSocketDisconnect, RuntimeError):
                            is_connected = False

        elif kind == 'on_chain_end' and event['name'] == 'SupervisorAgent' and not interrupt_caught:
            bot_message: BotMessage = event['data']['output']['structured_response']
            bot_message_dump = bot_message.model_dump()
            response_time = time.time() - message_received_at

            logger.debug(f"Agent Response content: {bot_message_dump}", extra={"user_id": user_id, "response_time": response_time})

            if is_connected:
                try:
                    await websocket.send_json(bot_message_dump)
                except (WebSocketDisconnect, RuntimeError):
                    is_connected = False
                    logger.debug("User disconnected during final response. Saved to DB.", extra={"user_id": user_id})

    return is_connected


@router.websocket("/ws/chat")
async def websocket_endpoint(
        websocket: WebSocket,
        user: Any = Depends(get_current_user_ws)
):
    await websocket.accept()
    user_id = user.id
    timezone = websocket.query_params.get("timezone", "UTC")
    config = RunnableConfig(configurable={"thread_id": user_id, "timezone": timezone})

    from main import get_agent
    default_agent = get_agent(websocket.app, Config.DEFAULT_MODEL)

    try:
        api_service = await get_google_service(user_id, timezone)
    except (ProviderNotConnectedError, RefreshError):
        api_service = None

    logger.info("User connected", extra={"user_id": user_id})
    await send_chat_history(websocket, default_agent, config, user_id)

    try:
        state = await default_agent.agent.aget_state(config)
        if state.next and state.tasks and state.tasks[0].interrupts:
            interrupt_value = state.tasks[0].interrupts[0].value
            if isinstance(interrupt_value, dict):
                await websocket.send_json({
                    "type": "approval_required",
                    "confirmation": interrupt_value['confirmation'],
                    "data": interrupt_value['data']
                })
    except Exception as e:
        logger.warning(f"Failed to recover interrupt state: {e}", extra={"user_id": user_id})

    is_connected = True
    while True:
        try:
            if not is_connected:
                break

            data = await websocket.receive_json()

            is_allowed, remaining = await check_ws_rate_limit(user_id)
            if not is_allowed:
                logger.warning("WebSocket rate limit exceeded", extra={"user_id": user_id})
                await websocket.send_json({
                    "type": "error",
                    "code": "RATE_LIMITED",
                    "content": "Too many messages. Please wait before sending more."
                })
                continue

            model_name = data.get("model") or Config.DEFAULT_MODEL
            agent = get_agent(websocket.app, model_name)

            logger.debug(f"Received message content: {data}", extra={"user_id": user_id, "model": model_name})
            is_connected = await process_message(websocket, agent, config, data, user_id, api_service)

        except WebSocketDisconnect:
            logger.info("User disconnected", extra={"user_id": user_id})
            break
        except ProviderNotConnectedError as e:
            logger.warning(f"Provider not connected: {e}", extra={"user_id": user_id})
            if is_connected:
                try:
                    await websocket.send_json({
                        "type": "error",
                        "code": "AUTH_REQUIRED",
                        "provider": "Google",
                        "content": "Please authenticate your Google account."
                    })
                except (WebSocketDisconnect, RuntimeError):
                    is_connected = False
        except RefreshError as e:
            logger.warning(f"Token refresh failed: {e}", extra={"user_id": user_id})
            try:
                api_service = await get_google_service(user_id, timezone)
            except Exception:
                api_service = None
            if is_connected:
                try:
                    await websocket.send_json({
                        "type": "error",
                        "code": "AUTH_EXPIRED",
                        "provider": "Google",
                        "content": "Please re-authenticate your Google account."
                    })
                except (WebSocketDisconnect, RuntimeError):
                    is_connected = False
        except (GenAIAPIError, GoogleGenerativeAIError) as e:
            logger.error(f"Model API error: {e}", extra={"user_id": user_id}, exc_info=True)
            if is_connected:
                try:
                    await websocket.send_json({
                        "type": "error",
                        "code": "MODEL_ERROR",
                        "content": "The AI model is temporarily unavailable. Please try again shortly."
                    })
                except (WebSocketDisconnect, RuntimeError):
                    is_connected = False
        except Exception as e:
            logger.error(f"Unexpected error processing message: {e}", extra={"user_id": user_id}, exc_info=True)
            if is_connected:
                try:
                    await websocket.send_json({
                        "type": "error",
                        "code": "INTERNAL_ERROR",
                        "content": "An unexpected error occurred. Please try again."
                    })
                except (WebSocketDisconnect, RuntimeError):
                    is_connected = False


@router.delete("/chat/clear")
async def clear_chat(user: Any = Depends(get_current_user_http)):
    try:
        await database.clear_thread(user.id)
        logger.info("Chat history cleared", extra={"user_id": user.id})
    except Exception as e:
        logger.error(f"Failed to clear chat: {e}", extra={"user_id": user.id}, exc_info=True)
        raise HTTPException(status_code=500, detail="Error occurred.")

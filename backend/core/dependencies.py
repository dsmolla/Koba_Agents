from fastapi import WebSocket, HTTPException, Header, WebSocketException, status
from google.auth.transport import requests

from core.supabase_client import get_supabase
from core.redis_client import redis_client
import logging
from google.oauth2 import id_token

logger = logging.getLogger(__name__)


async def get_current_user_ws(websocket: WebSocket):
    ticket = websocket.query_params.get("ticket")
    if not ticket:
        logger.warning("WebSocket connection attempt missing ticket")
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    user_id = await redis_client.get_ws_ticket(ticket)
    if not user_id:
        logger.warning("Invalid or expired WebSocket ticket", extra={"ticket": ticket})
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    logger.debug("WebSocket authentication successful", extra={"user_id": user_id})

    class User:
        def __init__(self, id):
            self.id = id

    return User(id=user_id)


async def get_current_user_http(authorization: str = Header(None)):
    if not authorization:
        logger.warning("HTTP request missing Authorization header")
        raise HTTPException(401, "Missing Token")
    token = authorization.replace("Bearer ", "")
    try:
        client = await get_supabase()
        user_response = await client.auth.get_user(token)
        user = user_response.user
        logger.debug("HTTP authentication successful", extra={"user_id": user.id})
        return user
    except Exception as e:
        logger.error(f"HTTP authentication failed: {e}")
        raise HTTPException(401, "Invalid Token")


async def verify_google_token(authorization: str = Header(None)):
    if not authorization:
        logger.warning("Google token missing Authorization header")
        raise HTTPException(401, "Missing Token")
    token = authorization.replace("Bearer ", "")
    try:
        id_info = id_token.verify_oauth2_token(token, requests.Request())
        logger.debug("Google token verified")
        return id_info
    except Exception as e:
        logger.error(f"Google token validation failed: {e}")
        raise HTTPException(401, "Invalid OIDC Token")

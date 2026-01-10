from fastapi import WebSocket, HTTPException, Header, WebSocketException, status
from supabase import Client, create_client

from config import Config
from core.db import db


auth_client: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)


async def get_current_user_ws(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    try:
        user_response = auth_client.auth.get_user(token)
        return user_response.user
    except Exception:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)


async def get_current_user_http(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(401, "Missing Token")
    token = authorization.replace("Bearer ", "")
    try:
        user_response = auth_client.auth.get_user(token)
        return user_response.user
    except Exception:
        raise HTTPException(401, "Invalid Token")


async def get_db():
    return db

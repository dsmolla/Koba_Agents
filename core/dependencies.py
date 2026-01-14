from fastapi import WebSocket, HTTPException, Header, WebSocketException, status

from core.db import db
from core.supabase_client import get_supabase


async def get_current_user_ws(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    try:
        client = await get_supabase()
        user_response = await client.auth.get_user(token)
        return user_response.user
    except Exception:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)


async def get_current_user_http(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(401, "Missing Token")
    token = authorization.replace("Bearer ", "")
    try:
        client = await get_supabase()
        user_response = await client.auth.get_user(token)
        return user_response.user
    except Exception:
        raise HTTPException(401, "Invalid Token")


async def get_db():
    return db

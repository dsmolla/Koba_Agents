import os

from fastapi import WebSocket, HTTPException, Header
from supabase import Client, create_client

from core.db import db

auth_client: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)


async def get_current_user_ws(websocket: WebSocket):
    """
    Extracts token from WebSocket headers or query params.
    Expected format: ws://...?token=eyJ...
    """
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=1008, reason="Missing Token")
        raise HTTPException(401, "Missing Token")

    try:
        user_response = auth_client.auth.get_user(token)
        return user_response.user
    except Exception as e:
        print(f"Auth Error: {e}")
        await websocket.close(code=1008, reason="Invalid Token")
        raise HTTPException(401, "Invalid Token")


async def get_current_user_http(authorization: str = Header(None)):
    """Standard HTTP Bearer Token extraction."""
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

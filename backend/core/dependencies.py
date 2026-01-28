from fastapi import WebSocket, HTTPException, Header, WebSocketException, status
from core.supabase_client import get_supabase
from core.redis_client import redis_client


async def get_current_user_ws(websocket: WebSocket):
    ticket = websocket.query_params.get("ticket")
    if not ticket:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    
    user_id = await redis_client.get_ws_ticket(ticket)
    if not user_id:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    # Minimal user object to satisfy existing code expectations
    class User:
        def __init__(self, id):
            self.id = id
            
    return User(id=user_id)


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

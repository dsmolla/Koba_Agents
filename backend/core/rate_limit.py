from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from core.redis_client import redis_client

# Requests per window
HTTP_RATE_LIMIT = 60
HTTP_WINDOW_SECONDS = 60

# Messages per window
WS_RATE_LIMIT = 10
WS_WINDOW_SECONDS = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limits HTTP endpoints by IP or user ID."""

    async def dispatch(self, request: Request, call_next):
        # Skip WebSocket upgrades (handled separately)
        if request.scope.get("type") == "websocket":
            return await call_next(request)

        # Skip non-rate-limited paths
        path = request.url.path
        if path in ["/docs", "/openapi.json", "/health"]:
            return await call_next(request)

        # Use user ID from auth header if present, otherwise IP
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            # Hash the token to create a consistent key without storing the token
            import hashlib
            key = f"http:user:{hashlib.sha256(auth_header.encode()).hexdigest()[:16]}"
        else:
            client_ip = request.client.host if request.client else "unknown"
            key = f"http:ip:{client_ip}"

        is_allowed, remaining = await redis_client.check_rate_limit(
            key, HTTP_RATE_LIMIT, HTTP_WINDOW_SECONDS
        )

        if not is_allowed:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": str(HTTP_WINDOW_SECONDS)}
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Limit"] = str(HTTP_RATE_LIMIT)
        return response


async def check_ws_rate_limit(user_id: str) -> tuple[bool, int]:
    """Check if user can send a WebSocket message."""
    return await redis_client.check_rate_limit(
        f"ws:user:{user_id}", WS_RATE_LIMIT, WS_WINDOW_SECONDS
    )

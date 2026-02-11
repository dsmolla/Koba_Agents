import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from core.db import database
from core.redis_client import redis_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    postgres_ok = True
    redis_ok = True

    try:
        async with database._pool.connection() as conn:
            await conn.execute("SELECT 1")
    except Exception as e:
        logger.warning(f"Health check: PostgreSQL ping failed: {e}")
        postgres_ok = False

    try:
        await redis_client.redis.ping()
    except Exception as e:
        logger.warning(f"Health check: Redis ping failed: {e}")
        redis_ok = False

    healthy = postgres_ok and redis_ok
    payload = {
        "status": "healthy" if healthy else "degraded",
        "postgres": "up" if postgres_ok else "down",
        "redis": "up" if redis_ok else "down",
    }
    return JSONResponse(content=payload, status_code=200 if healthy else 503)

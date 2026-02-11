import logging
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from google_client.api_service import APIServiceLayer

from core.db import database
from core.dependencies import get_current_user_http
from core.exceptions import ProviderNotConnectedError
from core.models import GoogleCredentials
from core.redis_client import redis_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.post("/google")
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


@router.get("/{provider}")
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


@router.delete("/{provider}")
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

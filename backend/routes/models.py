from fastapi import APIRouter, Response

from config import Config

router = APIRouter(tags=["models"])


@router.get("/models")
async def list_models(response: Response):
    # Model list is static per deployment — allow clients to cache for 1 hour
    response.headers["Cache-Control"] = "public, max-age=3600"
    return {
        "models": [
            {"id": model_id, "name": name}
            for model_id, name in Config.ALLOWED_MODELS.items()
        ],
        "default": Config.DEFAULT_MODEL,
    }

from fastapi import APIRouter

from config import Config

router = APIRouter(tags=["models"])


@router.get("/models")
async def list_models():
    return {
        "models": [
            {"id": model_id, "name": name}
            for model_id, name in Config.ALLOWED_MODELS.items()
        ],
        "default": Config.DEFAULT_MODEL,
    }

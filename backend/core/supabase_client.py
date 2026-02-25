from pathlib import PurePosixPath

from supabase import create_async_client, AsyncClient

from config import Config

supabase_client = None

_ALLOWED_MIME = {"text/plain", "application/pdf", "image/png", "image/jpeg", "text/csv"}
_MAX_BYTES = 50 * 1024 * 1024  # 50 MB


def _safe_path(path: str) -> str:
    p = PurePosixPath(path)
    if ".." in p.parts or p.is_absolute():
        raise ValueError(f"Invalid file path: {path}")
    return str(p)


async def get_supabase() -> AsyncClient:
    global supabase_client
    if supabase_client is None:
        supabase_client = await create_async_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    return supabase_client


async def download_from_supabase(path: str) -> bytes | None:
    _safe_path(path)
    client = await get_supabase()
    return await client.storage.from_(Config.SUPABASE_USER_FILE_BUCKET).download(path)


async def upload_to_supabase(path: str, file_bytes: bytes, mime_type: str = "text/plain") -> str | None:
    _safe_path(path)
    if mime_type not in _ALLOWED_MIME:
        raise ValueError(f"Disallowed MIME type: {mime_type}")
    if len(file_bytes) > _MAX_BYTES:
        raise ValueError("File exceeds 50MB size limit")
    client = await get_supabase()
    response = await client.storage.from_(Config.SUPABASE_USER_FILE_BUCKET).upload(path, file_bytes, {"content-type": mime_type})
    return response.path

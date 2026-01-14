from supabase import create_async_client, AsyncClient

from config import Config

supabase_client = None


async def get_supabase() -> AsyncClient:
    global supabase_client
    if supabase_client is None:
        supabase_client = await create_async_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    return supabase_client


async def download_from_supabase(path: str) -> bytes | None:
    client = await get_supabase()
    return await client.storage.from_(Config.SUPABASE_USER_FILE_BUCKET).download(path)


async def upload_to_supabase(path: str, file_bytes: bytes, mime_type="text/plain") -> str | None:
    client = await get_supabase()
    response = await client.storage.from_(Config.SUPABASE_USER_FILE_BUCKET).upload(path, file_bytes, {"content-type": mime_type})
    return response.path

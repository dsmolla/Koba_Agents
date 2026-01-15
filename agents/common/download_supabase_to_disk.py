import uuid
from pathlib import Path

import aiofiles

from core.supabase_client import download_from_supabase


async def download_to_disk(supabase_paths: list[str]) -> tuple[Path, list[str]]:
    downloaded_files = []
    folder_name = str(uuid.uuid4())
    download_folder = Path('.tmp') / Path(folder_name)
    download_folder.mkdir(parents=True, exist_ok=True)
    for path in supabase_paths:
        attachment_bytes = await download_from_supabase(path)
        filename = path.split("/")[1]  # user_id/filename
        async with aiofiles.open(download_folder / filename, mode="wb") as file:
            await file.write(attachment_bytes)

        downloaded_files.append(str(download_folder / filename))

    return download_folder, downloaded_files
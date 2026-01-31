import tempfile
from pathlib import Path

import aiofiles

from core.supabase_client import download_from_supabase


async def download_to_disk(supabase_paths: list[str]) -> tuple[Path, list[str]]:
    downloaded_files = []
    temp_dir = Path(tempfile.mkdtemp(prefix="koba_"))

    for path in supabase_paths:
        attachment_bytes = await download_from_supabase(path)
        if attachment_bytes is None:
            continue

        filename = Path(path).name

        file_path = temp_dir / filename
        async with aiofiles.open(file_path, mode="wb") as file:
            await file.write(attachment_bytes)

        downloaded_files.append(str(file_path))

    return temp_dir, downloaded_files

import asyncio
import logging
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Optional
from werkzeug.utils import secure_filename

from config import Config

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter to prevent message flooding."""

    def __init__(self, max_messages: int = Config.RATE_LIMIT_MESSAGES, window_seconds: int = Config.RATE_LIMIT_WINDOW):
        self.max_messages = max_messages
        self.window_seconds = window_seconds
        self.user_messages: dict[int, deque] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def check_rate_limit(self, user_id: int) -> tuple[bool, Optional[int]]:
        """
        Check if user has exceeded rate limit.
        Returns: (is_allowed, seconds_to_wait)
        """
        async with self._lock:
            current_time = time.time()
            user_queue = self.user_messages[user_id]

            # Remove old messages outside the window
            while user_queue and current_time - user_queue[0] > self.window_seconds:
                user_queue.popleft()

            # Check if user has exceeded limit
            if len(user_queue) >= self.max_messages:
                # Calculate how long to wait
                oldest_message_time = user_queue[0]
                wait_time = int(self.window_seconds - (current_time - oldest_message_time)) + 1
                logger.warning("Rate limit exceeded", extra={
                    'user_id': user_id,
                    'messages_in_window': len(user_queue),
                    'wait_seconds': wait_time
                })
                return False, wait_time

            # Add current message timestamp
            user_queue.append(current_time)
            return True, None


class FileSecurityValidator:
    """Validator for file uploads with security checks."""

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal attacks."""
        # Use werkzeug's secure_filename for basic sanitization
        safe_name = secure_filename(filename)

        # If secure_filename returns empty string (e.g., all non-ASCII), use a fallback
        if not safe_name:
            safe_name = f"file_{int(time.time())}"

        logger.debug("Filename sanitized", extra={
            'original': filename,
            'sanitized': safe_name
        })

        return safe_name

    @staticmethod
    def validate_file_size(file_size: int) -> tuple[bool, Optional[str]]:
        """Validate file size doesn't exceed limits."""
        if file_size > Config.MAX_FILE_SIZE:
            size_mb = file_size / (1024 * 1024)
            max_mb = Config.MAX_FILE_SIZE / (1024 * 1024)
            error_msg = f"File size ({size_mb:.2f}MB) exceeds maximum allowed ({max_mb:.2f}MB)"
            logger.warning("File size limit exceeded", extra={
                'file_size_bytes': file_size,
                'max_size_bytes': Config.MAX_FILE_SIZE
            })
            return False, error_msg
        return True, None

    @staticmethod
    def validate_file_extension(filename: str) -> tuple[bool, Optional[str]]:
        """Validate file extension is in allowed list."""
        file_ext = Path(filename).suffix.lower()

        if file_ext not in Config.ALLOWED_FILE_EXTENSIONS:
            error_msg = f"File type '{file_ext}' is not allowed. Allowed types: {', '.join(Config.ALLOWED_FILE_EXTENSIONS)}"
            logger.warning("File extension not allowed", extra={
                'extension': file_ext,
                'filename': filename
            })
            return False, error_msg

        return True, None

    @staticmethod
    async def check_user_storage_quota(telegram_id: int) -> tuple[bool, Optional[str]]:
        """Check if user has exceeded storage quota."""
        user_dir = Path(Config.USER_FILES_DIR) / str(telegram_id)

        if not user_dir.exists():
            return True, None

        # Calculate total storage used by user
        total_size = 0
        for file_path in user_dir.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size

        if total_size >= Config.MAX_USER_STORAGE:
            used_mb = total_size / (1024 * 1024)
            max_mb = Config.MAX_USER_STORAGE / (1024 * 1024)
            error_msg = f"Storage quota exceeded ({used_mb:.2f}MB / {max_mb:.2f}MB). Please delete some files."
            logger.warning("User storage quota exceeded", extra={
                'user_id': telegram_id,
                'used_bytes': total_size,
                'quota_bytes': Config.MAX_USER_STORAGE
            })
            return False, error_msg

        return True, None


class FileCleanupManager:
    """Manager for cleaning up old files independent of session timeout."""

    @staticmethod
    async def cleanup_old_files():
        """Clean up files older than FILE_RETENTION_HOURS."""
        user_files_dir = Path(Config.USER_FILES_DIR)

        if not user_files_dir.exists():
            return 0

        current_time = time.time()
        retention_seconds = Config.FILE_RETENTION_HOURS * 3600
        deleted_count = 0

        logger.debug("Starting file cleanup", extra={
            'retention_hours': Config.FILE_RETENTION_HOURS
        })

        for user_dir in user_files_dir.iterdir():
            if not user_dir.is_dir():
                continue

            for file_path in user_dir.rglob('*'):
                if not file_path.is_file():
                    continue

                try:
                    file_age = current_time - file_path.stat().st_mtime

                    if file_age > retention_seconds:
                        file_path.unlink()
                        deleted_count += 1
                        logger.debug("Old file deleted", extra={
                            'file_path': str(file_path),
                            'age_hours': file_age / 3600
                        })
                except Exception as e:
                    logger.error("Error deleting old file", extra={
                        'file_path': str(file_path),
                        'error': str(e)
                    }, exc_info=True)

        if deleted_count > 0:
            logger.info("File cleanup completed", extra={
                'files_deleted': deleted_count
            })

        return deleted_count

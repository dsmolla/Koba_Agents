from dotenv import load_dotenv
import os
from pathlib import Path


load_dotenv()


class Config:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    GOOGLE_OAUTH_CLIENT_TOKEN = os.getenv("GOOGLE_OAUTH_CLIENT_TOKEN")
    USER_TOKENS_DB = os.getenv("USER_TOKENS_DB", "user_tokens.db")
    CHECKPOINTER_DB = os.getenv("CHECKPOINTER_DB", "checkpoints.db")
    USER_SESSIONS_DIR = os.getenv("USER_SESSIONS_DIR", "user_sessions")
    USER_FILES_DIR = os.getenv("USER_FILES_DIR", "user_files")

    SECRET_KEY = os.getenv("SECRET_KEY")
    SECRET_KEY_SALT = os.getenv("SECRET_KEY_SALT")

    SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", 86400))  # 24 hours (increased from 1 hour)
    MAX_MESSAGE_LENGTH = 4096  # Telegram message limit
    MAX_MESSAGE_HISTORY = int(os.getenv("MAX_MESSAGE_HISTORY", 50))  # Maximum messages to keep in history

    # File handling settings
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 20 * 1024 * 1024))  # 20MB per file
    MAX_USER_STORAGE = int(os.getenv("MAX_USER_STORAGE", 100 * 1024 * 1024))  # 100MB per user
    FILE_RETENTION_HOURS = int(os.getenv("FILE_RETENTION_HOURS", 48))  # Keep files for 48 hours
    ALLOWED_FILE_EXTENSIONS = os.getenv("ALLOWED_FILE_EXTENSIONS", ".pdf,.doc,.docx,.xls,.xlsx,.txt,.csv,.png,.jpg,.jpeg,.gif,.zip").split(",")

    # Rate limiting
    RATE_LIMIT_MESSAGES = int(os.getenv("RATE_LIMIT_MESSAGES", 10))  # Max messages per window
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", 60))  # Window in seconds

    # Network timeout settings for Telegram API (in seconds)
    TELEGRAM_CONNECT_TIMEOUT = float(os.getenv("TELEGRAM_CONNECT_TIMEOUT", "30.0"))
    TELEGRAM_READ_TIMEOUT = float(os.getenv("TELEGRAM_READ_TIMEOUT", "60.0"))
    TELEGRAM_WRITE_TIMEOUT = float(os.getenv("TELEGRAM_WRITE_TIMEOUT", "60.0"))
    TELEGRAM_MEDIA_WRITE_TIMEOUT = float(os.getenv("TELEGRAM_MEDIA_WRITE_TIMEOUT", "120.0"))
    TELEGRAM_POOL_SIZE = int(os.getenv("TELEGRAM_POOL_SIZE", "32"))

    OAUTH_SCOPES = [
        'https://www.googleapis.com/auth/calendar',
        'https://mail.google.com/',
        'https://www.googleapis.com/auth/tasks',
        'https://www.googleapis.com/auth/drive'
    ]
    OAUTH_REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI")
    LANGGRAPH_DEBUG = os.getenv("LANGGRAPH_DEBUG", "False").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Webhook settings
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g., https://yourdomain.com
    WEBHOOK_SECRET_TOKEN = os.getenv("WEBHOOK_SECRET_TOKEN")
    WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "80"))
    WEBHOOK_MAX_CONNECTIONS = int(os.getenv("WEBHOOK_MAX_CONNECTIONS", "100"))

    @classmethod
    def validate(cls):
        errors = []

        if not cls.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN is not set in the environment variables.")
        if not cls.SECRET_KEY:
            errors.append("SECRET_KEY is not set in the environment variables.")
        if not cls.GOOGLE_OAUTH_CLIENT_TOKEN:
            errors.append("GOOGLE_OAUTH_CLIENT_TOKEN is not set in the environment variables.")

        # Webhook validation
        if not cls.WEBHOOK_URL:
            errors.append("WEBHOOK_URL is not set in the environment variables.")
        if not cls.WEBHOOK_SECRET_TOKEN:
            errors.append("WEBHOOK_SECRET_TOKEN is not set in the environment variables.")

        if errors:
            raise ValueError("Configuration errors:\n" + "\n".join(f"- {e}" for e in errors))
        Path(cls.USER_SESSIONS_DIR).mkdir(parents=True, exist_ok=True)
        
    @classmethod
    def get_user_session_path(cls, user_id) -> Path:
        return Path(cls.USER_SESSIONS_DIR) / f"{user_id}_session.json"

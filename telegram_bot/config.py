"""
Configuration module for Telegram Bot
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration settings for the Telegram bot"""

    # Telegram Bot Settings
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    # Google OAuth Settings
    CREDS_PATH = os.getenv("CREDS_PATH")

    # User Data Storage
    USER_TOKENS_DIR = Path(os.getenv("USER_TOKENS_DIR", "user_tokens"))
    USER_SESSIONS_DIR = Path(os.getenv("USER_SESSIONS_DIR", "user_sessions"))

    # LLM Settings
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

    # Bot Settings
    MAX_MESSAGE_LENGTH = 4096  # Telegram's max message length
    SESSION_TIMEOUT = 3600  # 1 hour in seconds
    PRINT_STEPS = os.getenv("PRINT_STEPS", "false").lower() == "true"

    # OAuth Settings
    # Using localhost redirect (must match what's in credentials.json)
    OAUTH_REDIRECT_URI = "http://localhost"
    OAUTH_SCOPES = [
        'https://www.googleapis.com/auth/calendar',
        'https://mail.google.com/',
        'https://www.googleapis.com/auth/tasks',
        'https://www.googleapis.com/auth/drive'
    ]

    @classmethod
    def validate(cls):
        """Validate that required configuration is present"""
        errors = []

        if not cls.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN is not set in environment variables")

        if not cls.CREDS_PATH:
            errors.append("CREDS_PATH is not set in environment variables")
        elif not os.path.exists(cls.CREDS_PATH):
            errors.append(f"Credentials file not found at {cls.CREDS_PATH}")

        if not cls.GOOGLE_API_KEY:
            errors.append("GOOGLE_API_KEY is not set in environment variables")

        if errors:
            raise ValueError(f"Configuration errors:\n" + "\n".join(f"- {e}" for e in errors))

        # Create necessary directories
        cls.USER_TOKENS_DIR.mkdir(exist_ok=True)
        cls.USER_SESSIONS_DIR.mkdir(exist_ok=True)

    @classmethod
    def get_user_token_path(cls, user_id: int) -> Path:
        """Get the path to a user's token file"""
        return cls.USER_TOKENS_DIR / f"user_{user_id}_token.json"

    @classmethod
    def get_user_session_path(cls, user_id: int) -> Path:
        """Get the path to a user's session file"""
        return cls.USER_SESSIONS_DIR / f"user_{user_id}_session.json"

from dotenv import load_dotenv
import os
from pathlib import Path


load_dotenv()


class Config:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    CLIENT_CREDS_PATH = os.getenv("CLIENT_CREDS_PATH")
    USER_TOKENS_DB = os.getenv("USER_TOKENS_DB", "user_tokens.db")
    USER_SESSIONS_DIR = os.getenv("USER_SESSIONS_DIR", "user_sessions")

    SECRET_KEY = os.getenv("SECRET_KEY")

    SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", 3600))  # 1 hour
    MAX_MESSAGE_LENGTH = 4096  # Telegram message limit

    OAUTH_SCOPES = [
        'https://www.googleapis.com/auth/calendar',
        'https://mail.google.com/',
        'https://www.googleapis.com/auth/tasks',
        'https://www.googleapis.com/auth/drive'
    ]
    OAUTH_REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI")
    LANGGRAPH_DEBUG = os.getenv("LANGGRAPH_DEBUG", "False").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls):
        errors = []

        if not cls.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN is not set in the environment variables.")
        if not cls.SECRET_KEY:
            errors.append("SECRET_KEY is not set in the environment variables.")
        if not cls.CLIENT_CREDS_PATH:
            errors.append("CREDS_PATH is not set in the environment variables.")
        elif not Path(cls.CLIENT_CREDS_PATH).is_file():
            errors.append(f"CREDS_PATH '{cls.CLIENT_CREDS_PATH}' does not point to a valid file.")
        
        if errors:
            raise ValueError("Configuration errors:\n" + "\n".join(f"- {e}" for e in errors))
        Path(cls.USER_SESSIONS_DIR).mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_creds_path(cls, user_id) -> Path | None:
        if cls.CLIENT_CREDS_PATH:
            return Path(cls.CLIENT_CREDS_PATH)
        
    @classmethod
    def get_user_session_path(cls, user_id) -> Path:
        return Path(cls.USER_SESSIONS_DIR) / f"{user_id}_session.json"

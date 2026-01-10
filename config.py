import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
    GOOGLE_OAUTH_CLIENT_TOKEN = os.getenv("GOOGLE_OAUTH_CLIENT_TOKEN")

    SECRET_KEY = os.getenv("SECRET_KEY")
    SECRET_KEY_SALT = os.getenv("SECRET_KEY_SALT")

    OAUTH_SCOPES = [
        'https://www.googleapis.com/auth/calendar',
        'https://mail.google.com/',
        'https://www.googleapis.com/auth/tasks',
        'https://www.googleapis.com/auth/drive'
    ]

    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls):
        errors = []

        if not cls.GEMINI_API_KEY:
            errors.append('GOOGLE_API_KEY environment variable is not set')
        if not cls.GOOGLE_OAUTH_CLIENT_TOKEN:
            errors.append('GOOGLE_OAUTH_CLIENT_TOKEN environment variable is not set')
        if not cls.SECRET_KEY:
            errors.append('SECRET_KEY environment variable is not set')
        if not cls.SECRET_KEY_SALT:
            errors.append('SECRET_KEY_SALT environment variable is not set')
        if not cls.SUPABASE_URL:
            errors.append('SUPABASE_URL environment variable is not set')
        if not cls.SUPABASE_KEY:
            errors.append('SUPABASE_KEY environment variable is not set')
        if not cls.SUPABASE_DB_URL:
            errors.append('SUPABASE_DB_URL environment variable is not set')

        if errors:
            raise ValueError("Configuration errors:\n" + "\n".join(f"- {e}" for e in errors))
